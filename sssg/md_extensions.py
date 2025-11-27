from pathlib import Path
from markdown import Extension
from markdown.treeprocessors import Treeprocessor
import xml.etree.ElementTree as etree

from typing import Optional


class LinkRewriterExtension(Extension):
    def __init__(self, **kwargs):
        self.src_filename: Optional[Path] = None
        self.dst_filename: Optional[Path] = None
        self.config = {
            "files_as_dirs": [False, "True if files_as_dirs is enabled"],
            "entrypoint": ["", "Entry path for the templater"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.treeprocessors.register(
            LinkRewriterTreeprocessor(self), "linkrewriter", 10
        )  # before LinkInlineProcessor

    def set_current_filenames(self, src: Path, dst: Path):
        """Override the current filenames."""
        self.src_filename = src
        self.dst_filename = dst


class LinkRewriterTreeprocessor(Treeprocessor):
    """Rewrite links in Markdown from original filesystem path to the final output path."""

    def __init__(self, extension: LinkRewriterExtension):
        super().__init__()
        self.extension = extension

        self.files_as_dirs: bool = self.extension.getConfig("files_as_dirs", False)

        entrypoint: str = self.extension.getConfig("entrypoint", "")
        self.entrypoint: Optional[Path] = (
            Path(entrypoint) if entrypoint and len(entrypoint) > 0 else None
        )

        exitpoint: str = self.extension.getConfig("exitpoint", "")
        self.exitpoint: Optional[Path] = (
            Path(exitpoint) if exitpoint and len(exitpoint) > 0 else None
        )

    def run(self, root: etree.Element) -> None:
        for child in root.iter("a"):
            href = child.get("href")
            converted_path = self.get_converted_path(href)
            if converted_path != href:
                child.set("href", converted_path)

    def get_converted_path(self, href: str) -> str:
        if (
            not self.extension.src_filename
            or not self.extension.dst_filename
            or not self.entrypoint
        ):
            # Not configured for translation
            return href
        if "://" in href:
            # Not a local path
            return href

        href_local = Path(href)
        if href_local.is_absolute():
            # Absolute path has no need for rewriting
            # It's also probably invalid, but we're not going to worry about that here
            return href

        href_abs = (
            (self.extension.src_filename.parent / href_local).resolve().absolute()
        )
        try:
            # If the file doesn't exist, don't attempt to rewrite it
            if not href_abs.exists():
                print(
                    " > In",
                    self.extension.src_filename,
                    "link to",
                    href,
                    "does not exist.",
                )
                return href
        except IOError:
            return href

        # Blindly calculate the relativeness of the href's final destination
        src_depth = len(self.extension.src_filename.parts)
        dst_depth = len(href_abs.parts)
        if self.files_as_dirs:
            # Compensate for the subdirectory
            dst_depth -= 1
        depth_distance = src_depth - dst_depth
        joiner = "./"
        if depth_distance > 0:
            joiner = "../" * depth_distance

        dst_rel = href_abs.relative_to(self.entrypoint)
        dst_basename = str(dst_rel.name).split(".")[0]
        if self.files_as_dirs:
            return f"{joiner}{dst_basename}/index.html"
        else:
            return f"{joiner}{dst_basename}.html"
