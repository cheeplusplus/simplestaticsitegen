from pathlib import Path
from markdown import Extension
from markdown.treeprocessors import Treeprocessor
import xml.etree.ElementTree as eTree

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

    def run(self, root: eTree.Element) -> None:
        for child in root.iter("a"):
            href = child.get("href")
            converted_path = self.get_converted_path(href, self.files_as_dirs)
            if converted_path != href:
                child.set("href", converted_path)
        for child in root.iter("img"):
            href = child.get("src")
            converted_path = self.get_converted_path(href)
            if converted_path != href:
                child.set("src", converted_path)

    def get_converted_path(self, href: str, files_as_dirs: bool = False) -> str:
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
        relative_parts = href_abs.relative_to(self.extension.src_filename, walk_up=True).parts
        relative_pathing = "/".join(relative_parts[:-1])
        if len(relative_pathing) > 0:
            relative_pathing += "/"

        dst_rel = href_abs.relative_to(self.entrypoint)
        dst_basename = str(dst_rel.name).split(".")[0]
        dst_suffixes = dst_rel.suffixes

        # Remove the always-stripped file extensions
        if ".j2" in dst_suffixes:
            dst_suffixes.remove(".j2")
        if ".sssg-copy" in dst_suffixes:
            dst_suffixes.remove(".sssg-copy")

        # Calculate the final href
        final_path = f"{relative_pathing}{dst_basename}"
        if ".html" in dst_suffixes or ".md" in dst_suffixes:
            if files_as_dirs:
                final_path += "/"
            else:
                final_path += ".html"
        else:
            final_path += ".".join(dst_suffixes)

        return final_path
