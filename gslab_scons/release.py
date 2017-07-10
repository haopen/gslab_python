import re
import os
import sys
import _release_tools
from _exception_classes import ReleaseError


def main():
    inspect_repo()

    # Extract information about the clone from its .git directory
    repo, organisation, branch = _release_tools.extract_dot_git()
    user_config_cache = misc.()
    # Determine the version number
    try:
        version = next(arg for arg in sys.argv if re.search("^version=", arg))
    except:
        raise ReleaseError('No version specified.')

    version = re.sub('^version=', '', version)

    # Determine whether the user has specified the no_zip option
    dont_zip    = 'no_zip' in sys.argv
    zip_release = not dont_zip

     # Read a list of files to release to Google Drive
    release_files = list()
    for root, _, files in os.walk('./release'):
        for file_name in files:
            # Do not release .DS_Store
            if not re.search("\.DS_Store", file_name):
                release_files.append(os.path.join(root, file_name))

    # Specify the local release directory
    if branch == 'master':
        name   = repo
        branch = ''
    else:
        name = "%s-%s" % (repo, branch)
    local_release = '/%s/%s/' % (user_config_cache, name)
    local_release = local_release + version + '/'
    
    _release_tools.release(vers              = version, 
                           DriveReleaseFiles = release_files,
                           local_release     = local_release, 
                           org               = organisation, 
                           repo              = repo,
                           target_commitish  = branch,
                           zip_release       = zip_release)


def inspect_repo():
    '''Ensure the repo is ready for release.'''
    if not _release_tools.up_to_date(mode = 'scons'):
        raise ReleaseError('SCons targets not up to date.')  
    elif not _release_tools.up_to_date(mode = 'git'):
        print "Warning: `scons` has run since your latest git commit.\n"
        response = raw_input("Would you like to continue anyway? (y|n)\n")
        if response in ['N', 'n']: 
            sys.exit()


if __name__ == '__main__':
    main()
