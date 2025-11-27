import shutil
from pathlib import Path
from typing import Optional
from urllib import parse, request
from .templater import Templater
from .util import restructure_file_as_dir, find_files, BuildError


def process_template(tmpl: Templater, source_filename: Path, dest_filename: Path, **kwargs) -> None:
    '''Read a source file and save the template output.'''

    with open(source_filename, "r", encoding="utf-8") as f:
        content = f.read()

    output = tmpl.generate_html(content, source_filename, dest_filename, **kwargs)

    with open(dest_filename, "w", encoding="utf-8") as f:
        f.write(output)


def process_md_template(tmpl: Templater, source_filename: Path, dest_filename: Path, **kwargs) -> None:
    '''Read a Markdown file and save the template output.'''

    with open(source_filename, "r", encoding="utf-8") as f:
        content = f.read()

    output = tmpl.generate_markdown(content, source_filename, dest_filename, **kwargs)

    with open(dest_filename, "w", encoding="utf-8") as f:
        f.write(output)


def process_copy_operation(source_filename: Path, dest_filename: Path) -> None:
    '''Parse a SSSG-COPY file and save the target to the destination.'''

    with open(source_filename, "r", encoding="utf-8") as f:
        target_url = f.read()

    if not target_url:
        return

    (scheme, _, _, _, _, _) = parse.urlparse(target_url)

    if not scheme:
        # Probably a local path, relative or otherwise
        abs_target = Path(target_url)
        if not abs_target.is_absolute():
            abs_target = (Path(source_filename).parent / target_url).resolve()
        if abs_target.exists():
            shutil.copy2(abs_target, dest_filename)
        else:
            raise BuildError(f"Unable to find source file {target_url}")
    else:
        # Save the URL to a file
        request.urlretrieve(target_url, dest_filename)


def process_directory(source_dir: str, dest_dir: str, files_as_dirs: bool = False, wipe_first: bool = False,
                      ignore_paths: Optional[list[str]] = None, debug: bool = False) -> None:
    '''Process a source directory and save results to destination.'''

    # Validate source directory
    source_path = Path(source_dir).absolute()
    if not source_path.exists():
        raise FileNotFoundError("Source directory does not exist.")

    # Find all files in source
    contents = find_files(source_path, ignore_paths)

    # Handle destination directory
    dest_path = Path(dest_dir).absolute()
    if wipe_first and dest_path.is_dir():
        shutil.rmtree(dest_path)

    # Prepare templater
    tmpl = Templater(source_path, files_as_dirs)

    # Copy to output directory
    for curr_src_file in contents:
        # Get the target path
        pp = curr_src_file.parts[len(source_path.parts):]
        curr_dest_file = Path(dest_path, *pp)

        # Make sure it exists
        curr_dest_dir = curr_dest_file.parent
        if not curr_dest_dir.is_dir():
            curr_dest_dir.mkdir(exist_ok=True)

        if debug:
            print(f" > {curr_src_file}")

        if curr_src_file.suffix == ".j2" or curr_src_file.suffix == ".md":
            # Run anything ending in .j2 as a template
            # Assume .md files are templates so they get turned into HTML

            curr_dest_path_pure = curr_dest_file.with_suffix("")
            ptr_height = len(pp)

            if ".md" in curr_src_file.suffixes:
                # Process Markdown template
                curr_dest_path_pure = curr_dest_path_pure.with_suffix(".html")
                (curr_dest_path_pure, ptr) = restructure_file_as_dir(files_as_dirs, curr_dest_path_pure, ptr_height)

                try:
                    process_md_template(tmpl, curr_src_file, curr_dest_path_pure, path_to_root=ptr)
                except Exception as err:
                    raise BuildError(f"Failed processing markdown file: /{'/'.join(pp)}, got error: {err}") from err
            else:
                # Process default template
                (curr_dest_path_pure, ptr) = restructure_file_as_dir(files_as_dirs, curr_dest_path_pure, ptr_height)

                try:
                    process_template(tmpl, curr_src_file, curr_dest_path_pure, path_to_root=ptr)
                except Exception as err:
                    raise BuildError(f"Failed processing template file: /{'/'.join(pp)}, got error: {err}") from err
        elif curr_src_file.suffix == ".sssg-copy":
            # Copy softlinks

            curr_dest_path_pure = curr_dest_file.with_suffix("")

            try:
                process_copy_operation(curr_src_file, curr_dest_path_pure)
            except Exception as err:
                raise BuildError(f"Failed file copy: /{'/'.join(pp)}, got error: {err}") from err

        else:
            # Copy everything else

            shutil.copy2(curr_src_file, curr_dest_file)
