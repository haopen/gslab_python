import re
import os
import sys
from _exception_classes import ReleaseError
from _release_tools import (create_size_dictionary, up_to_date, 
                            extract_dot_git, release)

'''
Make a release from an SCons directory using:
    python -m gslab_scons.release version=<version name here>
where <version name here> is the name of the version that
the user wishes to release. As an example, to release version
v1.2.1 of a directory, one would run:
    python -m gslab_scons.release version=v1.2.1
from the root of the directory. 
Including the option `no_zip` will prevent the release files
from being zipped before their release to Google Drive.
'''

if __name__ == '__main__':

    # Ensure that the directory's targets are up to date
    if not up_to_date(mode = 'scons'):
        raise ReleaseError('SCons targets not up to date.')
    if not up_to_date(mode = 'git'):
        print "WARNING: `scons` has run since your latest git commit.\n"
        response = raw_input("Would you like to continue anyway? (y|n)\n")
        if response in ['N', 'n']: 
            sys.exit()

    #== Issue warnings if the files versioned in release are too large ========
    # Set soft size limits in MB
    file_MB_limit  = 2
    total_MB_limit = 500 
 
    bytes_in_MB = 1000000

    # Compile a list of files that are not versioned.
    if os.path.exists('./.gitignore'):
        git_ignore = open('./.gitignore', 'rU')
        ignored_files = git_ignore.readlines()
        ignored_files = map(lambda s: os.path.join('./', s.strip()), 
                            ignored_files)
        git_ignore.close()

    release_sizes = create_size_dictionary('./release')
    versioned_sizes = dict()

    for file_name in release_sizes.keys():
        if file_name not in ignored_files:
            versioned_sizes[file_name] = release_sizes[file_name]

            size  = release_sizes[file_name]
            limit = file_MB_limit * bytes_in_MB

            if size > limit and file_name:
                print "\nWARNING: the versioned file " + file_name + \
                    " is larger than " + str(file_MB_limit) + " MB.\n" + \
                    "Versioning files of this size is discouraged.\n"
                response = raw_input("Would you like to continue anyway? (y|n)\n")
                if response in ['N', 'n']: 
                    sys.exit()

    total_size  = sum(versioned_sizes.values())
    total_limit = total_MB_limit * bytes_in_MB

    if total_size > total_limit:
        print "\nWARNING: the versioned files in /release/ are together " + \
            "larger than " + str(total_MB_limit) + " MB.\n" + \
            "Versioning this much content is discouraged.\n"
        response = raw_input("Would you like to continue anyway? (y|n)\n")
        if response in ['N', 'n']: 
            sys.exit()

    #==========================================================================

    # Extract information about the clone's repository, organisation,
    # and branch from its .git directory
    repo, organisation, branch = extract_dot_git()

    # Determine the version number
    try:
        version = next(arg for arg in sys.argv if re.search("^version=", arg))
    except:
        raise ReleaseError('No version specified.')

    version = re.sub('^version=', '', version)

    # Determine whether the user has specified the zip option as a
    # command-line argument.
    dont_zip    = 'no_zip' in sys.argv
    zip_release = not dont_zip

     # Read a list of files to release to Google Drive
    release_files = list()
    for root, _, files in os.walk('./release'):
        for file_name in files:
            release_files.append(os.path.join(root, file_name))

    # Specify the local release directory
    USER = os.environ['USER']
    if branch == 'master':
        name   = repo
        branch = ''
    else:
        name = "%s-%s" % (repo, branch)
    local_release = '/Users/%s/Google Drive/release/%s/' % (USER, name)
    local_release = local_release + version + '/'
    
    release(vers              = version, 
            DriveReleaseFiles = release_files,
            local_release     = local_release, 
            org               = organisation, 
            repo              = repo,
            target_commitish  = branch,
            zip_release       = zip_release)
