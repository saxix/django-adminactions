import re
from sphinx import addnodes, roles
from sphinx.util.compat import Directive
from sphinx.writers.html import SmartyPantsHTMLTranslator

simple_option_desc_re = re.compile(
    r'([-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)')


def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_crossref_type(
        directivename="templatetag",
        rolename="ttag",
        indextemplate="pair: %s; template tag"
    )
    app.add_crossref_type(
        directivename="templatefilter",
        rolename="tfilter",
        indextemplate="pair: %s; template filter"
    )
    app.add_crossref_type(
        directivename="fieldlookup",
        rolename="lookup",
        indextemplate="pair: %s; field lookup type",
    )
    app.add_config_value('next_version', '0.0', True)
    app.add_directive('versionadded', VersionDirective)
    app.add_directive('versionchanged', VersionDirective)
    app.add_crossref_type(
        directivename="release",
        rolename="release",
        indextemplate="pair: %s; release",
    )

class VersionDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}
    version_text = {
        'deprecated':       'Deprecated in %s.',
        'versionchanged':   'Changed in %s.',
        'versionadded':     'New in %s.',
    }

    def run(self):
        env = self.state.document.settings.env
        arg0 = self.arguments[0]
        ret = []
        node = addnodes.versionmodified()
        ret.append(node)

        node['type'] = self.name
        if env.config.next_version == arg0:
            version = "Development version"
            link = None
        else:
            version = arg0
            link = 'release-%s' % arg0

        node['version'] = version
        # inodes, messages = self.state.inline_text(self.version_text[self.name] % version, self.lineno+1)
        # node.extend(inodes)
        if link:
            text = ' Please see the changelog <%s>' % link
            xrefs = roles.XRefRole()('std:ref', text, text, self.lineno, self.state)
            node.extend(xrefs[0])
        env.note_versionchange(node['type'], node['version'], node, self.lineno)
        return ret

