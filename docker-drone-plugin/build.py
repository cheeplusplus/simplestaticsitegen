import os
import sssg

input_dir = "./"
if 'PLUGIN_SOURCE' in os.environ:
    input_dir = os.environ['PLUGIN_SOURCE']

target_dir = os.path.join(input_dir, "build")
if 'PLUGIN_TARGET' in os.environ:
    target_dir = os.environ['PLUGIN_TARGET']

sssg.process_directory(input_dir, target_dir)
