"""
Sphinx plugins for Django documentation.
"""
import json
import os
import re

from sphinx import __version__ as sphinx_ver
from sphinx import addnodes
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.util.compat import Directive
from sphinx.util.console import bold
from sphinx.writers.html import SmartyPantsHTMLTranslator

# RE for option descriptions without a '--' prefix
simple_option_desc_re = re.compile(r"([-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)")


def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_crossref_type(
        directivename="templatetag",
        rolename="ttag",
        indextemplate="pair: %s; template tag",
    )
    app.add_crossref_type(
        directivename="templatefilter",
        rolename="tfilter",
        indextemplate="pair: %s; template filter",
    )
    app.add_crossref_type(
        directivename="fieldlookup",
        rolename="lookup",
        indextemplate="pair: %s; field lookup type",
    )
    app.add_description_unit(
        directivename="django-admin",
        rolename="djadmin",
        indextemplate="pair: %s; django-admin command",
        parse_node=parse_django_admin_node,
    )
    app.add_description_unit(
        directivename="django-admin-option",
        rolename="djadminopt",
        indextemplate="pair: %s; django-admin command-line option",
        parse_node=parse_django_adminopt_node,
    )
    # app.add_config_value('django_next_version', '0.0', True)
    # app.add_directive('versionadded', VersionDirective)
    # app.add_directive('versionchanged', VersionDirective)
    app.add_builder(DjangoStandaloneHTMLBuilder)


class VersionDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        ret = []
        node = addnodes.versionmodified()
        ret.append(node)
        if self.arguments[0] == env.config.django_next_version:
            node["version"] = "Development version"
        else:
            node["version"] = self.arguments[0]
        node["type"] = self.name
        if len(self.arguments) == 2:
            inodes, messages = self.state.inline_text(self.arguments[1], self.lineno + 1)
            node.extend(inodes)
            if self.content:
                self.state.nested_parse(self.content, self.content_offset, node)
            ret = ret + messages
        env.note_versionchange(node["type"], node["version"], node, self.lineno)
        return ret


class DjangoHTMLTranslator(SmartyPantsHTMLTranslator):
    """
    Django-specific reST to HTML tweaks.
    """

    # Don't use border=1, which docutils does by default.
    def visit_table(self, node):
        self._table_row_index = 0  # Needed by Sphinx
        self.body.append(self.starttag(node, "table", CLASS="docutils"))

    # <big>? Really?
    def visit_desc_parameterlist(self, node):
        self.body.append("(")
        self.first_param = 1
        self.param_separator = node.child_text_separator

    def depart_desc_parameterlist(self, node):
        self.body.append(")")

    if sphinx_ver < "1.0.8":
        #
        # Don't apply smartypants to literal blocks
        #
        def visit_literal_block(self, node):
            self.no_smarty += 1
            SmartyPantsHTMLTranslator.visit_literal_block(self, node)

        def depart_literal_block(self, node):
            SmartyPantsHTMLTranslator.depart_literal_block(self, node)
            self.no_smarty -= 1

    #
    # Turn the "new in version" stuff (versionadded/versionchanged) into a
    # better callout -- the Sphinx default is just a little span,
    # which is a bit less obvious that I'd like.
    #
    # FIXME: these messages are all hardcoded in English. We need to change
    # that to accomodate other language docs, but I can't work out how to make
    # that work.
    #
    version_text = {
        "deprecated": "Deprecated in Django %s",
        "versionchanged": "Changed in Django %s",
        "versionadded": "New in Django %s",
    }

    def visit_versionmodified(self, node):
        self.body.append(self.starttag(node, "div", CLASS=node["type"]))
        title = "%s%s" % (
            self.version_text[node["type"]] % node["version"],
            len(node) and ":" or ".",
        )
        self.body.append('<span class="title">%s</span> ' % title)

    def depart_versionmodified(self, node):
        self.body.append("</div>\n")

    # Give each section a unique ID -- nice for custom CSS hooks
    def visit_section(self, node):
        old_ids = node.get("ids", [])
        node["ids"] = ["s-" + i for i in old_ids]
        node["ids"].extend(old_ids)
        SmartyPantsHTMLTranslator.visit_section(self, node)
        node["ids"] = old_ids


def parse_django_admin_node(env, sig, signode):
    command = sig.split(" ")[0]
    env._django_curr_admin_command = command
    title = "django-admin.py %s" % sig
    signode += addnodes.desc_name(title, title)
    return sig


def parse_django_adminopt_node(env, sig, signode):
    """A copy of sphinx.directives.CmdoptionDesc.parse_signature()"""
    from sphinx.domains.std import option_desc_re

    count = 0
    firstname = ""
    for m in option_desc_re.finditer(sig):
        optname, args = m.groups()
        if count:
            signode += addnodes.desc_addname(", ", ", ")
        signode += addnodes.desc_name(optname, optname)
        signode += addnodes.desc_addname(args, args)
        if not count:
            firstname = optname
        count += 1
    if not count:
        for m in simple_option_desc_re.finditer(sig):
            optname, args = m.groups()
            if count:
                signode += addnodes.desc_addname(", ", ", ")
            signode += addnodes.desc_name(optname, optname)
            signode += addnodes.desc_addname(args, args)
            if not count:
                firstname = optname
            count += 1
    if not firstname:
        raise ValueError
    return firstname


class DjangoStandaloneHTMLBuilder(StandaloneHTMLBuilder):
    """
    Subclass to add some extra things we need.
    """

    name = "djangohtml"

    def finish(self):
        super().finish()
        self.info(bold("writing templatebuiltins.js..."))
        xrefs = self.env.domaindata["std"]["objects"]
        templatebuiltins = {
            "ttags": [
                n
                for ((t, n), (l, a)) in xrefs.items()  # noqa
                if t == "templatetag" and l == "ref/templates/builtins"  # noqa
            ],
            "tfilters": [
                n
                for ((t, n), (l, a)) in xrefs.items()  # noqa
                if t == "templatefilter" and l == "ref/templates/builtins"  # noqa
            ],
        }
        outfilename = os.path.join(self.outdir, "templatebuiltins.js")
        with open(outfilename, "wb") as fp:
            fp.write("var django_template_builtins = ")
            json.dump(templatebuiltins, fp)
            fp.write(";\n")
