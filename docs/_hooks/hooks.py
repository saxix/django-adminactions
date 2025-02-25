# mypy: disable-error-code="typeddict-unknown-key"
from datetime import datetime

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page
from mkdocs.utils.templates import TemplateContext


def on_pre_build(config: MkDocsConfig) -> None:
    pass


def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, files: Files) -> None:
    pass


def on_page_context(context: TemplateContext, nav: Navigation, page: Page, config: MkDocsConfig) -> None:
    context["build_date"] = datetime.now().strftime("%a, %d, %b %Y - %H:%M")
    context["config"] = config
