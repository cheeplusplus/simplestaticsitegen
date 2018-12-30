import argparse
from . import process_directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source directory")
    parser.add_argument("destination", help="Destination directory")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete contents of destination directory before copying")
    parser.add_argument("--files-as-dirs", action="store_true", help="Turn templated files into directories (Jekyll style)")
    parser.add_argument("-i", "--ignore", action="store_const", help="Ignore glob (gitignore style, comma seperated)")

    args = parser.parse_args()

    ignore_paths = []
    if args.ignore:
        ignore_paths = args.ignore.split(",")

    print("Processing.")
    process_directory(args.source, args.destination, files_as_dirs=args.files_as_dirs, wipe_first=args.delete, ignore_paths=ignore_paths)
    print("Done.")


if __name__ == "__main__":
    main()
