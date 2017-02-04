import os
import yaml
import gslab_scons.misc as misc

def build_rclone(target, source, env):
    '''Build a SCons target by downloading a file via the rclone interface.

        See rclone.org for more details on rclone.

        Uses env['CL_ARG'] to specify 'sync' or 'copy'. Defaults to 'copy'.

    Parameters
    ----------
    target: string or list 
        The target(s) of the SCons command.
    source: string or list
        The source(s) of the SCons command. The first source specified
        should be a yaml file specifying the files to downloaded and from
        what remote. E.g.,
        ```
        dropbox:
            dropbox_folder1/child_folder: local_folder
            dropbox_folder1/child_folder: local_folder2

        drive:
            drive_folder/child_folder: local_folder3
        ```
    
    Options
    -------
    Setting env['dropbox'], env['drive'], etc. will replace the remote names with the 
    value assigned. For example, if downloads.yaml specifies 'dropbox' as a remote name,
    but your local computer has named this remote 'dropbox_business', then setting 
    `env['dropbox'] = 'dropbox_business'` will replace the name before calling rclone.
    '''
    # Preliminaries
    source      = misc.make_list_if_string(source)
    source_file = str(source[0])
    target      = misc.make_list_if_string(target)
    target_dir  = os.path.dirname(str(target[0]))
    log_file    = os.path.join(target_dir, 'sconscript.log')

    misc.check_code_extension(source_file, 'yaml')

    # Import list of downloads
    downloads = yaml.load(open(source_file, 'rU'))

    # Rename remote based on env variable
    for key in downloads.keys():
        try:
            downloads[env[key]] = downloads[key]
            del downloads[key]
        except:
            pass

    # Determine whether to sync or clone from remote
    sync_copy = misc.command_line_arg(env)
    if sync_copy != 'sync':
        sync_copy = 'copy'

    # Execute downloads
    for remote in downloads.keys():
        for objective in downloads[remote].keys():
            targ_dir = downloads[remote][objective]
            os.system("rclone %s %s:%s %s > %s" % \
                (sync_copy, remote, objective, targ_dir, log_file))

    return None
