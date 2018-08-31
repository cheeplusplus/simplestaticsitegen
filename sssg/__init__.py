import argparse
import os
import shutil
import pathlib
import json
from jinja2 import Environment, FileSystemLoader, Markup
from jinja2.ext import Extension
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

        default_template_dir = os.path.join(os.path.dirname(__file__), "default_templates")
        template_paths.append(default_template_dir)

        self.jinja = Environment(loader=FileSystemLoader(template_paths))
        self.jinja.filters["markdown"] = lambda text: Markup(self.md.convert(text))

    def read_metadata(self, content):
        '''Attempt to read metadata from a file.'''
        post = frontmatter.loads(content)
        return (post.content, post.metadata)

    def generate_string(self, content, **kwargs):
        '''Generate output given a template string and content.'''
        (con, meta) = self.read_metadata(content)

        # Handle load_json
        extra_data = {}
        if "load_json" in meta:
            with open(meta["load_json"]) as f:
                extra_data = json.load(f)

        template = self.jinja.from_string(con)
        return (template.render(**kwargs, **meta, **extra_data), meta)

    def generate_html(self, content, **kwargs):
        '''Generate output given template HTML content.'''
        (con, meta) = self.generate_string(content, **kwargs)
        return con

    def generate_markdown(self, content, **kwargs):
        '''Generate output given template Markdown content.'''
        # Convert Markdown to HTML
        (con, meta) = self.generate_string(content, **kwargs)

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

    output = tmpl.generate_html(content, **kwargs)

    with open(dest_filename, "w") as f:
        f.write(output)


def process_md_template(tmpl, source_filename, dest_filename, **kwargs):
    '''Read a Markdown file and save the template output.'''

    with open(source_filename, "r") as f:
        content = f.read()

    output = tmpl.generate_markdown(content, **kwargs)

    with open(dest_filename, "w") as f:
        f.write(output)


def find_files(dir):
    '''Find files in the source directory.'''

    with os.scandir(dir) as it:
        for entry in it:
            if entry.is_file():
                yield os.path.join(entry.path)
            if entry.is_dir() and entry.name != "." and entry.name != ".." and entry.name != ".templates":
                yield from find_files(entry.path)


def process_directory(source_dir, dest_dir, wipe_first=False):
    '''Process a source directory and save results to destination.'''

    if not os.path.exists(source_dir):
        raise FileNotFoundError("Source directory does not exist.")

    contents = find_files(source_dir)

    if wipe_first:
        shutil.rmtree(dest_dir)

    templater = Templater(source_dir)

    # Copy to output directory
    for src_path in contents:
        # Get the target path
        p = pathlib.Path(src_path)
        pp = p.parts[1:]
        dest_path = pathlib.Path(dest_dir, *pp)

        # Make sure it exists
        dest_dir_path = os.path.dirname(dest_path)
        if not os.path.exists(dest_dir_path):
            os.makedirs(dest_dir_path)

        # Run anything ending in .j2 as a template
        # Assume .md files are templates so they get turned into HTML
        if src_path.endswith(".j2") or src_path.endswith(".md"):
            dest_path_pure = dest_path.with_suffix("")

            ptr = ""
            ptr_height = len(p.parts) - 1
            if ptr_height > 1:
                ptr = "".join(map(lambda x: "../", range(ptr_height - 1)))

            if src_path.endswith(".md.j2") or src_path.endswith(".md"):
                # Process Markdown template
                dest_path_pure = dest_path_pure.with_suffix(".html")
                process_md_template(templater, src_path, dest_path_pure, path_to_root=ptr)
            else:
                # Process default template
                process_template(templater, src_path, dest_path_pure, path_to_root=ptr)
        else:
            # Copy everything else
            shutil.copy2(src_path, dest_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source directory")
    parser.add_argument("destination", help="Destination directory")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete contents of destination directory before copying")

    args = parser.parse_args()

    print("Running.")
    process_directory(args.source, args.destination, args.delete)
    print("Done.")
