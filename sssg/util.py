import typing
from collections.abc import Callable
from pathlib import Path
from pathmatch import gitmatch
from typing import Generator, Optional, Iterable


class BuildError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


def restructure_file_as_dir(files_as_dirs: bool, current_path: Path, current_height=0, new_filename="index.html") -> \
        tuple[Path, str]:
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
        return current_path, ptr

    target_dir = basedir / filename
    if not target_dir.exists():
        target_dir.mkdir()

    return target_dir / new_filename, ptr


def find_files(start_dir: Path, ignore_paths: Optional[Iterable[str]] = None, relative_path: str = "") -> \
        Generator[Path, None, None]:
    '''Find files in the source directory.'''

    ignore_these: list[Callable[[str], bool]] = []
    if ignore_paths is not None:
        if not isinstance(ignore_paths, list):
            # Coerce to list
            ignore_paths = list(ignore_paths)

        # Construct matchers
        ignore_these = [(lambda fn: gitmatch.match(p, fn)) for p in ignore_paths]

    for entry in Path(start_dir).iterdir():
        relative_file = relative_path + "/" + entry.name

        if entry.is_file():
            # Handle ignore paths
            if any(i(relative_file) for i in ignore_these):
                # Skip this entry
                continue

            yield entry
        if entry.is_dir() and entry.name != "." and entry.name != ".." and entry.name != ".templates":
            yield from find_files(entry, ignore_paths=ignore_paths, relative_path=relative_file)
