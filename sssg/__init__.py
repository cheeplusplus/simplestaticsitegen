import os
import shutil
import sys
from pathlib import Path
from pathmatch import gitmatch
import importlib.util
import inspect
import json
from jinja2 import Environment, FileSystemLoader
from markdown import Markdown, Extension
from markupsafe import Markup
import frontmatter
import urllib.request
from typing import Generator, Optional
from .filters import add_custom_filters


class BuildError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class Templater(object):
    '''Build templates.'''

    def __init__(self, source_dir: str, extra_jinja_filters: dict[str, any] = None, extra_md_extensions: list[Extension] = None):
        # Register regular and extra Markdown extensions
        md_extensions = [
            'markdown.extensions.nl2br',
            'markdown.extensions.tables',
            'pymdownx.magiclink',
            'pymdownx.betterem',
            'pymdownx.tilde',
            'pymdownx.emoji',
            'pymdownx.tasklist',
            'pymdownx.superfences'
        ]
        if extra_md_extensions:
            for ext in extra_md_extensions:
                md_extensions.append(ext)

        self.md = Markdown(extensions=md_extensions)
        
        # Don't use the built-in link as we want to be able to rewrite them
        self.md.inlinePatterns.deregister("link")

        template_paths = []

        template_dir = os.path.join(source_dir, ".templates")
        if os.path.exists(template_dir):
            template_paths.append(template_dir)

        cur_lib_dir = os.path.dirname(inspect.getabsfile(Templater))
        default_template_dir = os.path.join(cur_lib_dir, "default_templates")
        template_paths.append(default_template_dir)

        self.jinja = Environment(loader=FileSystemLoader(template_paths))
        
        # Register built-in custom Jinja filters
        self.jinja.filters["markdown"] = lambda text: Markup(self.md.convert(text))
        add_custom_filters(self.jinja.filters)
        
        # Register extra Jinja filters
        if extra_jinja_filters:
            for name, func in extra_jinja_filters.items():
                self.jinja.filters[name] = func

    def read_metadata(self, content: str) -> tuple[str, dict[str, str]]:
        '''Attempt to read metadata from a file.'''
        post = frontmatter.loads(content)
        return (post.content, post.metadata)

    def render_redirect(self, meta: dict[str, str]) -> str:
        template = self.jinja.get_template("redirect.html")
        return template.render(**meta)

    def generate_string(self, content: str, source_filename: str, **kwargs) -> tuple[str, dict[str, str]]:
        '''Generate output given a template string and content.'''
        (con, meta) = self.read_metadata(content)

        # Handle load_json
        extra_data = {}
        if "load_json" in meta:
            p = os.path.join(os.path.dirname(source_filename), meta["load_json"])
            with open(p, "r", encoding="utf-8") as f:
                extra_data = json.load(f)

        template = self.jinja.from_string(con)
        template.filename = source_filename

        return (template.render(**kwargs, **meta, **extra_data), meta)

    def generate_html(self, content: str, source_filename: str, **kwargs) -> str:
        '''Generate output given template HTML content.'''
        (con, meta) = self.generate_string(content, source_filename, **kwargs)
        if "redirect_url" in meta:
            return self.render_redirect(meta)

        return con

    def generate_markdown(self, content: str, source_filename: str, **kwargs):
        '''Generate output given template Markdown content.'''
        # Convert Markdown to HTML
        (con, meta) = self.generate_string(content, source_filename, **kwargs)
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


def process_template(tmpl: Templater, source_filename: str, dest_filename: str, **kwargs) -> None:
    '''Read a source file and save the template output.'''

    with open(source_filename, "r", encoding="utf-8") as f:
        content = f.read()

    output = tmpl.generate_html(content, source_filename, **kwargs)

    with open(dest_filename, "w", encoding="utf-8") as f:
        f.write(output)


def process_md_template(tmpl: Templater, source_filename: str, dest_filename: str, **kwargs) -> None:
    '''Read a Markdown file and save the template output.'''

    with open(source_filename, "r", encoding="utf-8") as f:
        content = f.read()

    output = tmpl.generate_markdown(content, source_filename, **kwargs)

    with open(dest_filename, "w", encoding="utf-8") as f:
        f.write(output)


def process_copy_operation(source_filename: str, dest_filename: str) -> None:
    '''Parse a SSSG-COPY file and save the target to the destination.'''

    with open(source_filename, "r", encoding="utf-8") as f:
        target_url = f.read()

    if not target_url:
        return

    (scheme, _, _, _, _, _) = urllib.parse.urlparse(target_url)

    if not scheme:
        # Probably a local path, relative or otherwise
        abs_target = Path(target_url)
        if (not abs_target.is_absolute()):
            abs_target = (Path(source_filename).parent / target_url).resolve()
        if abs_target.exists():
            shutil.copy2(abs_target, dest_filename)
        else:
            raise BuildError(f"Unable to find source file {target_url}")
    else:
        # Save the URL to a file
        urllib.request.urlretrieve(target_url, dest_filename)


def restructure_file_as_dir(files_as_dirs, current_path: Path, current_height=0, new_filename="index.html") -> tuple[Path, str]:
    '''Restructure "file.md" as "file/index.html", imitating Jekyll'''

    basedir = current_path.parent
    filename = current_path.stem

    if files_as_dirs and filename != "index":
        # Only increment height if not an index file
        current_height = current_height + 1

    ptr = ""
    if current_height > 1:
        ptr = "".join(map(lambda x: "../", range(current_height - 1)))

    if not files_as_dirs or filename == "index":
        # Don't continue
        return (current_path, ptr)

    target_dir = basedir / filename
    if not target_dir.exists():
        target_dir.mkdir()

    return (target_dir / new_filename, ptr)


def find_files(dir: str, ignore_paths: Optional[list[str]] = None, relative_path: str = "") -> Generator[str, None, None]:
    '''Find files in the source directory.'''

    ignore_these = []
    if ignore_paths and len(ignore_paths) > 0:
        if not isinstance(ignore_paths, list):
            # Coerce to list
            ignore_paths = list(ignore_paths)

        # Construct matchers
        ignore_these = [(lambda fn: gitmatch.match(p, fn)) for p in ignore_paths]

    with os.scandir(dir) as it:
        for entry in it:
            relative_file = relative_path + "/" + entry.name

            if entry.is_file():
                # Handle ignore paths
                if any(i(relative_file) for i in ignore_these):
                    # Skip this entry
                    continue

                yield os.path.join(entry.path)
            if entry.is_dir() and entry.name != "." and entry.name != ".." and entry.name != ".templates":
                yield from find_files(entry.path, ignore_paths=ignore_paths, relative_path=relative_file)


def process_directory(source_dir: str, dest_dir: str, files_as_dirs: bool = False, wipe_first: bool = False, ignore_paths: Optional[list[str]] = None, custom_filter_module_path: str = None, custom_md_extension_module_path: str = None, debug: bool = False) -> None:
    '''Process a source directory and save results to destination.'''

    # Validate and load custom filter module
    custom_jinja_filters = None
    if custom_filter_module_path:
        custom_filter_module_path_abs = os.path.abspath(custom_filter_module_path)
        import_spec = importlib.util.spec_from_file_location("jinja_loader", custom_filter_module_path_abs)
        import_mod = importlib.util.module_from_spec(import_spec)
        sys.modules["jinja_loader"] = import_mod
        import_spec.loader.exec_module(import_mod)
        if hasattr(import_mod, "SSSG_JINJA_FILTERS"):
            custom_jinja_filters = import_mod.SSSG_JINJA_FILTERS
        else:
            print("Failed to import custom Jinja filters module")

    # Validate and load custom Markdown extension module
    custom_md_extensions = None
    if custom_md_extension_module_path:
        custom_md_extension_module_path_abs = os.path.abspath(custom_md_extension_module_path)
        import_spec = importlib.util.spec_from_file_location("md_ext_loader", custom_md_extension_module_path_abs)
        import_mod = importlib.util.module_from_spec(import_spec)
        sys.modules["md_ext_loader"] = import_mod
        import_spec.loader.exec_module(import_mod)
        if hasattr(import_mod, "SSSG_MD_EXTENSIONS"):
            custom_md_extensions = import_mod.SSSG_MD_EXTENSIONS
        else:
            print("Failed to import custom Markdown extensions module")

    # Validate source directory
    source_dir = os.path.abspath(source_dir)
    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError("Source directory does not exist.")

    # Find all files in source
    contents = find_files(source_dir, ignore_paths)

    # Handle destination directory
    dest_dir = os.path.abspath(dest_dir)
    if wipe_first and os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    # Prepare templater
    templater = Templater(source_dir, extra_jinja_filters=custom_jinja_filters, extra_md_extensions=custom_md_extensions)

    # Copy to output directory
    for src_path in contents:
        # Get the target path
        p = Path(src_path)
        pp = p.parts[len(source_path.parts):]
        dest_path = Path(dest_dir, *pp)

        # Make sure it exists
        dest_dir_path = os.path.dirname(dest_path)
        if not os.path.exists(dest_dir_path):
            os.makedirs(dest_dir_path)
        
        if debug:
            print(f" > {src_path}")

        if src_path.endswith(".j2") or src_path.endswith(".md"):
            # Run anything ending in .j2 as a template
            # Assume .md files are templates so they get turned into HTML

            dest_path_pure = dest_path.with_suffix("")
            ptr_height = len(pp)

            if src_path.endswith(".md.j2") or src_path.endswith(".md"):
                # Process Markdown template
                dest_path_pure = dest_path_pure.with_suffix(".html")
                (dest_path_pure, ptr) = restructure_file_as_dir(files_as_dirs, dest_path_pure, ptr_height)

                try:
                    process_md_template(templater, src_path, dest_path_pure, path_to_root=ptr)
                except Exception as err:
                    raise BuildError(f"Failed processing markdown file: /{'/'.join(pp)}, got error: {err}") from err
            else:
                # Process default template
                (dest_path_pure, ptr) = restructure_file_as_dir(files_as_dirs, dest_path_pure, ptr_height)

                try:
                    process_template(templater, src_path, dest_path_pure, path_to_root=ptr)
                except Exception as err:
                    raise BuildError(f"Failed processing template file: /{'/'.join(pp)}, got error: {err}") from err
        elif src_path.endswith(".sssg-copy"):
            # Copy softlinks

            dest_path_pure = dest_path.with_suffix("")

            try:
                process_copy_operation(src_path, dest_path_pure)
            except Exception as err:
                raise BuildError(f"Failed file copy: /{'/'.join(pp)}, got error: {err}") from err

        else:
            # Copy everything else

            shutil.copy2(src_path, dest_path)
