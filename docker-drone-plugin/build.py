import os
import sssg

input_dir = "./"
if 'PLUGIN_SOURCE' in os.environ:
    input_dir = os.environ['PLUGIN_SOURCE']

target_dir = os.path.join(input_dir, "build")
if 'PLUGIN_TARGET' in os.environ:
    target_dir = os.environ['PLUGIN_TARGET']

files_as_dirs = False
if 'PLUGIN_FILESASDIRS' in os.environ:
    files_as_dirs = True

ignore_paths = None
if 'PLUGIN_IGNORE' in os.environ:
    ignore_paths = os.environ['PLUGIN_IGNORE'].split(',')

print("Processing.")
sssg.process_directory(input_dir, target_dir, files_as_dirs=files_as_dirs, ignore_paths=ignore_paths)
print("Done.")
