import os
import shutil
from pathlib import Path
from pathmatch import gitmatch
import inspect
import json
from jinja2 import Environment, FileSystemLoader, Markup
from markdown import Markdown
import frontmatter


class Templater(object):
    '''Build templates.'''

    def __init__(self, source_dir):
        self.md = Markdown(extensions=[
            'markdown.extensions.nl2br'
        ])

        template_paths = []

        template_dir = os.path.join(source_dir, ".templates")
        if os.path.exists(template_dir):
            template_paths.append(template_dir)

        cur_lib_dir = os.path.dirname(inspect.getabsfile(Templater))
        default_template_dir = os.path.join(cur_lib_dir, "default_templates")
        template_paths.append(default_template_dir)

        self.jinja = Environment(loader=FileSystemLoader(template_paths))
        self.jinja.filters["markdown"] = lambda text: Markup(self.md.convert(text))

    def read_metadata(self, content):
        '''Attempt to read metadata from a file.'''
        post = frontmatter.loads(content)
        return (post.content, post.metadata)

    def generate_string(self, content, source_filename, **kwargs):
        '''Generate output given a template string and content.'''
        (con, meta) = self.read_metadata(content)

        # Handle load_json
        extra_data = {}
        if "load_json" in meta:
            p = os.path.join(os.path.dirname(source_filename), meta["load_json"])
            with open(p, "r") as f:
                extra_data = json.load(f)

        template = self.jinja.from_string(con)
        return (template.render(**kwargs, **meta, **extra_data), meta)

    def generate_html(self, content, source_filename, **kwargs):
        '''Generate output given template HTML content.'''
        (con, meta) = self.generate_string(content, source_filename, **kwargs)
        return con

    def generate_markdown(self, content, source_filename, **kwargs):
        '''Generate output given template Markdown content.'''
        # Convert Markdown to HTML
        (con, meta) = self.generate_string(content, source_filename, **kwargs)

        # Metadata processing
        # Handle template_name
        template_name = "markdown.html"
        if "template_name" in meta:
            template_name = "{}.html".format(meta["template_name"])

        # Output template as final HTML
        template = self.jinja.get_template(template_name)
        return template.render(md_content=con, **kwargs, **meta)


def process_template(tmpl, source_filename, dest_filename, **kwargs):
    '''Read a source file and save the template output.'''

    with open(source_filename, "r") as f:
        content = f.read()

    output = tmpl.generate_html(content, source_filename, **kwargs)

    with open(dest_filename, "w") as f:
        f.write(output)


def process_md_template(tmpl, source_filename, dest_filename, **kwargs):
    '''Read a Markdown file and save the template output.'''

    with open(source_filename, "r") as f:
        content = f.read()

    output = tmpl.generate_markdown(content, source_filename, **kwargs)

    with open(dest_filename, "w") as f:
        f.write(output)


def restructure_file_as_dir(current_path, new_filename="index.html"):
    '''Restructure "file.md" as "file/index.html", imitating Jekyll'''
    basedir = current_path.parent
    filename = current_path.stem
    if filename == "index":
        # Don't modify an index file
        return current_path

    target_dir = basedir / filename
    if not target_dir.exists():
        target_dir.mkdir()

    return target_dir / new_filename


def find_files(dir, ignore_paths=None, relative_path=""):
    '''Find files in the source directory.'''

    ignore_these = []
    if ignore_paths:
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


def process_directory(source_dir, dest_dir, files_as_dirs=False, wipe_first=False, ignore_paths=None):
    '''Process a source directory and save results to destination.'''

    # Validate source directory
    source_dir = os.path.abspath(source_dir)
    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError("Source directory does not exist.")

    # Find all files in source
    contents = find_files(source_dir, ignore_paths)

    # Handle destination directory
    dest_dir = os.path.abspath(dest_dir)
    if wipe_first:
        shutil.rmtree(dest_dir)

    # Prepare templater
    templater = Templater(source_dir)

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

        # Run anything ending in .j2 as a template
        # Assume .md files are templates so they get turned into HTML
        if src_path.endswith(".j2") or src_path.endswith(".md"):
            dest_path_pure = dest_path.with_suffix("")

            ptr = ""
            ptr_height = len(pp)
            if ptr_height > 1:
                ptr = "".join(map(lambda x: "../", range(ptr_height - 1)))

            if src_path.endswith(".md.j2") or src_path.endswith(".md"):
                # Process Markdown template
                dest_path_pure = dest_path_pure.with_suffix(".html")
                if files_as_dirs:
                    dest_path_pure = restructure_file_as_dir(dest_path_pure)
                process_md_template(templater, src_path, dest_path_pure, path_to_root=ptr)
            else:
                # Process default template
                if files_as_dirs:
                    dest_path_pure = restructure_file_as_dir(dest_path_pure)
                process_template(templater, src_path, dest_path_pure, path_to_root=ptr)
        else:
            # Copy everything else
            shutil.copy2(src_path, dest_path)
