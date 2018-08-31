import argparse
from . import process_directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source directory")
    parser.add_argument("destination", help="Destination directory")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete contents of destination directory before copying")

    args = parser.parse_args()

    print("Running.")
    process_directory(args.source, args.destination, args.delete)
    print("Done.")


if __name__ == "__main__":
    main()
