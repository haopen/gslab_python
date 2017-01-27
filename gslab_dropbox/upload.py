#! /usr/bin/env python
import argparse
from gslab_dropbox import gslab_dropbox

parser = argparse.ArgumentParser(description = 'Upload files to dropbox.')
parser.add_argument('local_path',   type = str, help = "Path to local file or directory.")
parser.add_argument('dropbox_path', type = str, help = "Path to dropbox file or directory.")
parser.add_argument('--no-recursive', dest = 'recursive', action = 'store_const',
					const = False, default = True, 
					help = "Prevent recursive uploads for directories. (Default: Recursive upload.)")
parser.add_argument('--overwrite', dest = 'overwrite', action = 'store_const',
					const = True, default = False, 
					help = "Overwrite existing file/directory. (Default: False.")


args = parser.parse_args()
box  = gslab_dropbox()
box.upload(args.local_path, args.dropbox_path, args.recursive, args.overwrite)

print("%s successfully uploaded to %s" % (args.local_path, args.dropbox_path))