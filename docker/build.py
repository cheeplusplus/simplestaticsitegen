import os
import sssg

input_dir = "./"
if 'INPUT_SOURCE' in os.environ:
    input_dir = os.environ['INPUT_SOURCE']

target_dir = os.path.join(input_dir, "build")
if 'INPUT_TARGET' in os.environ:
    target_dir = os.environ['INPUT_TARGET']

files_as_dirs = False
if 'INPUT_FILESASDIRS' in os.environ and os.environ['INPUT_FILESASDIRS'] == 'true':
    files_as_dirs = True

ignore_paths = None
if 'INPUT_IGNORE' in os.environ:
    ignore_paths = os.environ['INPUT_IGNORE'].split(',')

print("Processing.")
sssg.process_directory(input_dir, target_dir, files_as_dirs=files_as_dirs, ignore_paths=ignore_paths)
print("Done.")
