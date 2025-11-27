import inspect
import json
from jinja2 import Environment, FileSystemLoader
from markdown import Markdown
from markupsafe import Markup
import frontmatter
from pathlib import Path
from .filters import add_custom_filters
from .md_extensions import LinkRewriterExtension


class Templater(object):
    '''Build templates.'''

    def __init__(self, source_dir: Path, files_as_dirs: bool):
        self.link_rewriter = LinkRewriterExtension(files_as_dirs=files_as_dirs, entrypoint=str(source_dir))
        self.md = Markdown(extensions=[
            'markdown.extensions.nl2br',
            'markdown.extensions.tables',
            'pymdownx.magiclink',
            'pymdownx.betterem',
            'pymdownx.tilde',
            'pymdownx.emoji',
            'pymdownx.tasklist',
            'pymdownx.superfences',
            self.link_rewriter,
        ])

        template_paths: list[Path] = []

        template_dir = source_dir / ".templates"
        if template_dir.is_dir():
            template_paths.append(template_dir)

        cur_lib_dir = Path(inspect.getabsfile(Templater)).parent
        default_template_dir = cur_lib_dir / "default_templates"
        template_paths.append(default_template_dir)

        self.jinja = Environment(loader=FileSystemLoader(template_paths))
        self.jinja.filters["markdown"] = lambda text: Markup(self.md.convert(text))
        add_custom_filters(self.jinja.filters)

    def read_metadata(self, content: str) -> tuple[str, dict[str, str]]:
        '''Attempt to read metadata from a file.'''
        post = frontmatter.loads(content)
        return (post.content, post.metadata)

    def render_redirect(self, meta: dict[str, str]) -> str:
        template = self.jinja.get_template("redirect.html")
        return template.render(**meta)

    def generate_string(self, content: str, source_filename: Path, dest_filename: Path, **kwargs) -> tuple[
        str, dict[str, str]]:
        '''Generate output given a template string and content.'''
        (con, meta) = self.read_metadata(content)

        # Handle load_json
        extra_data = {}
        if "load_json" in meta:
            p = os.path.join(os.path.dirname(source_filename), meta["load_json"])
            with open(p, "r", encoding="utf-8") as f:
                extra_data = json.load(f)

        # Update markdown paths
        self.link_rewriter.set_current_filenames(source_filename, dest_filename)

        template = self.jinja.from_string(con)
        template.filename = str(source_filename)

        return (template.render(**kwargs, **meta, **extra_data), meta)

    def generate_html(self, content: str, source_filename: Path, dest_filename: Path, **kwargs) -> str:
        '''Generate output given template HTML content.'''
        (con, meta) = self.generate_string(content, source_filename, dest_filename, **kwargs)
        if "redirect_url" in meta:
            return self.render_redirect(meta)

        return con

    def generate_markdown(self, content: str, source_filename: Path, dest_filename: Path, **kwargs):
        '''Generate output given template Markdown content.'''
        # Convert Markdown to HTML
        (con, meta) = self.generate_string(content, source_filename, dest_filename, **kwargs)
        if "redirect_url" in meta:
            return self.render_redirect(meta)

        # Metadata processing
        # Handle template_name
        template_name = "markdown.html"
        if "template_name" in meta:
            template_name = "{}.html".format(meta["template_name"])

        # Output template as final HTML
        template = self.jinja.get_template(template_name)
        return template.render(md_content=con, **kwargs, **meta)
