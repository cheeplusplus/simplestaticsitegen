import argparse
from . import process_directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source directory")
    parser.add_argument("destination", help="Destination directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug output")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete contents of destination directory before copying")
    parser.add_argument("--files-as-dirs", action="store_true", help="Turn templated files into directories (Jekyll style)")
    parser.add_argument("-i", "--ignore", action="store", help="Ignore glob (gitignore style, comma seperated)")
    parser.add_argument('--load-module', action="store", help="Path to a custom Jinja filter module")
    parser.add_argument('--customize-module', action="store", help="Path to a customizer module")

    args = parser.parse_args()

    ignore_paths = []
    if args.ignore:
        ignore_paths = args.ignore.split(",")

    print("Processing.")
    process_directory(args.source, args.destination, debug=args.verbose, files_as_dirs=args.files_as_dirs, wipe_first=args.delete, ignore_paths=ignore_paths, customize_module_path=args.customize_module)
    print("Done.")


if __name__ == "__main__":
    main()
