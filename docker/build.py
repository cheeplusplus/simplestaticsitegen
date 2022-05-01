import os
import sssg

input_dir = "./"
if 'INPUT_SOURCE' in os.environ and len(os.environ['INPUT_SOURCE']):
    input_dir = os.environ['INPUT_SOURCE']

target_dir = os.path.join(input_dir, "build")
if 'INPUT_TARGET' in os.environ and len(os.environ['INPUT_TARGET']):
    target_dir = os.environ['INPUT_TARGET']

files_as_dirs = False
if 'INPUT_FILESASDIRS' in os.environ and os.environ['INPUT_FILESASDIRS'] == 'true':
    files_as_dirs = True

ignore_paths = None
if 'INPUT_IGNORE' in os.environ and len(os.environ['INPUT_IGNORE']) > 0:
    ignore_paths = os.environ['INPUT_IGNORE'].split(',')

debug = False
if 'SSSG_DEBUG' in os.environ and os.environ['SSSG_DEBUG'] == 'true':
    print("Starting SSSG action.")
    print("Current directory:", os.getcwd())
    print("Input:", input_dir)
    print("Target:", target_dir)
    print("Files as dirs?", files_as_dirs)
    print("Ignore paths:", ignore_paths)

print("Processing data...")
sssg.process_directory(input_dir, target_dir, files_as_dirs=files_as_dirs, ignore_paths=ignore_paths, debug=debug)
print("Done.")
