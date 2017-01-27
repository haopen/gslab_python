import dropbox
import os
import shutil
import getpass

class gslab_dropbox(object):
    '''
    Methods for gslab interaction with dropbox.
    '''

    def __init__(self):
        token = getpass.getpass('Please enter OAuth Token: ')
        self.session = dropbox.dropbox.Dropbox(oauth2_access_token = token)

    # Universal methods
    def upload(self, local_path, dropbox_path, recursive = True,
                    overwrite = False, chunk_size = 100 * 1024 * 1024):
        '''
        Either uploads a file or a directory based on the local path. See 
        file and directory specific functions for more details on arguments.
        '''
        if os.path.isfile(local_path):
            self.dropbox_file_upload(dropbox_path, local_path, overwrite, chunk_size)

        elif os.path.isdir(local_path):
            self.dropbox_directory_upload(dropbox_path, local_path, recursive, overwrite)

        else:
            raise Exception('%s is neither a local file nor a local directory.' % local_path)
    

    def download(self, local_path, dropbox_path, revision = None, overwrite = False,
                                                    recursive = False, add_pages = None):
        '''
        Either download a file or a directory based on the local path. See 
        file and directory specific functions for more details on arguments.
        '''
        if os.path.isfile(local_path):
            self.dropbox_file_download(dropbox_path, local_path, 
                                       revision, overwrite)

        elif os.path.isdir(local_path):
            self.dropbox_directory_download(dropbox_path, local_path, 
                                            recursive, add_pages, overwrite)

        else:
            raise Exception('%s is neither a local file nor a local directory.' % local_path)


    def remove(self, dropbox_path, recursive = False):
        '''
        Either removes a dropbox file or a dropbox directory based on the local path.  
        See file and directory specific functions for more details on arguments.
        '''
        if self.dropbox_file_exists(dropbox_path):
            self.dropbox_file_remove(dropbox_path)

        elif self.dropbox_directory_exists(dropbox_path):
            self.dropbox_directory_remove(dropbox_path, recursive)

        else:
            raise Exception('%s is neither a file nor a directory on dropbox.' % local_path)


    # File Specific Methods
    def dropbox_file_exists(self, dropbox_file_path):
        '''
        True if file exists on Dropbox. False if not.
        Required Arguments
            dropbox_file_path: path to a file on Dropbox from root. 
        '''
        try:
            metadata = self.session.files_get_metadata(dropbox_file_path)
            if type(metadata) == dropbox.files.FileMetadata:
                return True
            else:
                return False
        except:
            return False
    
    
    def dropbox_file_remove(self, dropbox_file_path):
        '''
        Remove file on Dropbox.
        Required Arguments
            dropbox_file_path: path to a file on Dropbox from root.
        '''
        # Check if file for removal exists.
        if not self.dropbox_file_exists(dropbox_file_path):
            raise Exception('Specified file does not exist on Dropbox.')

        # Remove file.
        else:
            self.session.files_delete(dropbox_file_path)
    
    
    def dropbox_file_download(self, dropbox_file_path, local_file_path, 
                              revision = None, overwrite = False):
        '''
        Download file from dropbox
        Required Arguments
            dropbox_file_path: path to a file on Dropbox from root.
            local_file_path: path to new local file from working directory.
        Optional Arguments
            revision (numeric): revision number of file to download
            overwrite (boolean): overwrite file in local_file_path, if one exists
        '''
        # Check if file for download exists
        if not self.dropbox_file_exists(dropbox_file_path):
            raise Exception('Specified file path does not exist on Dropbox.')

        # Check if local file exists and cannot be overwritten.
        elif (os.path.isfile(local_file_path)) and (overwrite != True):
            raise Exception('Specified download file path already exists locally.') 

        # Download file
        else:
            # Check if directory for local download exists. If not, make it.
            local_directory_path = os.path.dirname(local_file_path)
            if not os.isdir(local_directory_path):
                os.makedirs(local_directory_path)
            # Download
            self.session.files_download_to_file(local_file_path, dropbox_file_path, revision)
               
    
    def dropbox_file_upload(self, dropbox_file_path, local_file_path, 
                            overwrite = False, chunk_size = 100 * 1024 * 1024):
        '''
        Upload file to Dropbox. Will create entire path to file if necessary.
        Required Arguments
            dropbox_file_path: path to a file on Dropbox from root.
            local_file_path: path to a local file from working directory.
        Optional Arguments
            overwrite (boolean): overwrite file on Dropbox if it exists.
            chunk_size (numeric): request size for Dropbox uploads.
        '''
        # Check the chunk size is not too high for Dropbox API
        if not chunk_size <= 150 * 1024 * 1024:
            raise Exception('The Dropbox API does not accept requests over 150MB ' +
                            'Specify a chunk size no more than 150 * 1024 * 1024')

        # Check if local file for upload exists.
        elif not os.path.exists(local_file_path):
            raise Exception('Local file specified for upload does not exist.')
    
        # Check if dropbox file exists and cannot be overwritten
        elif overwrite != True and self.dropbox_file_exists(dropbox_file_path):
            raise Exception('Specified file path already exists on Dropbox, but overwrite is not True')
        
        # Upload file
        else:
            local_file_size = os.path.getsize(local_file_path)
            
            with open(local_file_path, 'rU') as f:
                # Handle small files quickly
                if local_file_size <= chunk_size:
                    upload_file = f.read()
                    self.session.files_upload(upload_file, dropbox_file_path)
                
                # Handle large files
                else:
                    # Start Dropbox upload session for file.
                    session_start_result = self.session.files_upload_session_start(f.read(0))
                    upload_session_id    = session_start_result.session_id

                    cursor = dropbox.files.UploadSessionCursor(session_id = upload_session_id, offset = f.tell())
                    commit = dropbox.files.CommitInfo(path = dropbox_file_path)
                    
                    # Append chunks of file to upload session while the file is too big to read in one go.
                    while f.tell() < local_file_size:
                        self.session.files_upload_session_append_v2(f.read(chunk_size), cursor)
                        cursor.offset = f.tell()
                        
                    # When the file can be read in one go, read it and finish the upload session.
                    self.session.files_upload_session_finish(f.read(chunk_size), cursor, commit)
                

    # Directory Methods
    def dropbox_directory_exists(self, dropbox_directory_path):
        '''
        True if directory exists on Dropbox. False if not.
        Required Arguments
            dropbox_directory_path: path to a Dropbox directory from root.
        '''
        try:
            metadata = self.session.files_get_metadata(dropbox_directory_path)
            if type(metadata) == dropbox.files.FolderMetadata:
                return True
            else:
                return False
        except:
            return False

    
    def dropbox_directory_list(self, dropbox_directory_path, 
                               add_pages = None, recursive = False, name_only = False):
        '''
        List contents of a Dropbox directory. Returns a dictionary with keys indexing (ordered) 
        metadata pages from Dropbox and values as the the metadata pages.
        Required Arguments
            dropbox_directory_path: path to a Dropbox directory from root.
        Optional Arguments
            add_pages (numeric): number of additional pages of metadata to read and bind to dictionary.
            recursive (boolean): list contents of specified folder and all subfolders.
            name_only (boolean): return only name attributes from metadata. 
        '''
        # Check that Dropbox directory exists 
        if not self.dropbox_directory_exists(dropbox_directory_path):
            raise Exception('Specified directory does not exist on Dropbox')
        
        # Create dictionary to hold metadata from Dropbox directory 
        else:
            contents = {}
            # Get first page of metadata and bind it to the dictionary at key 0.
            page = self.session.files_list_folder(dropbox_directory_path, recursive = recursive)
            contents[0] = self.make_dropbox_directory_contents(page, name_only)
            
            # Page through metadata and bind to ordered dictionary keys until there's no more metadata or add_pages is hit.
            i = 1
            while (page.has_more == True) and (i <= add_pages):
                page = self.session.files_list_folder_continue(page.cursor)
                contents[1] = self.make_dropbox_directory_contents(page, name_only)
                i += 1
            return contents
            
    
    def make_dropbox_directory_contents(self, page, name_only):
        '''
        Helper function for dropbox_directory_list that adds metadata to dictionary of pages (i.e. content).
        Required Arguments
            page: a page of metadata from Dropbox Python SDK
            name_only (boolean): return only name attributes from metadata.
        '''
        if name_only == True:
            # Make a list of the name of each entry for all the entries on a page.
            content = [page.entries[entry].name for entry in range(len(page.entries))]
        else:
            content = page.entries
        return content
    
    
    def dropbox_directory_remove(self, dropbox_directory_path, 
                                 recursive = False):
        '''
        Remove directory if it exists and is empty.
        Required Arguments
            dropbox_directory_path: path to a Dropbox directory from root.
        Optional Arguments:
            recursive (boolean): remove non-empty directory and all sub-directories.
        '''
        # Check that Dropbox directory exists. 
        if not self.dropbox_directory_exists(dropbox_directory_path):
            raise Exception('Specified directory does not exist on Dropbox.')
        
        # Check that removal is recursive or that Dropbox directory is empty.  
        elif (recursive != True) and (len(self.dropbox_directory_list(dropbox_directory_path)[0]) > 0):
            raise Exception('Specified directory on Dropbox is not empty and recursive is not set to True.')
        
        # Remove directory on Dropbox
        else: 
            self.session.files_delete(dropbox_directory_path)
    
    
    def dropbox_directory_make(self, dropbox_directory_path,
                               handle_conflict = ''):
        '''
        Make new directory. Prefers autorename to overwrite if both specified.
        Required Arguments
            dropbox_directory_path: path to a Dropbox directory from root.
        Optional Arguments:
            handle_conflict ('', 'overwrite', or 'autorename'): how to hand conflict if a directory exists at same path.
                '': raises dropbox.files.CreareFolderError on conflict
                overwrite: recursively remove directory at path and create new one. 
                autorename: implement the Dropbox autorename procedure.
        '''
        # Check that handle_conflict is correctly specified.
        if not handle_conflict in ['', 'overwrite', 'autorename']:
            raise Exception("The handle_conflict argument must be '',  overwrite, or autorename")
        
        # Check that a conflicted directory will be handled.
        elif (self.dropbox_directory_exists(dropbox_directory_path)) and (handle_conflict == ''):
            raise Exception('The Dropbox directory already exists but the handle_conflict argument is not specified. ' + 
                            'The handle_conflict argument can either "overwrite" the existing directory or ' + 
                            'implement the Dropbox autorename procedure')
        
        # Make the directory
        else:
            # Don't handle conflicts.
            if handle_conflict == '':
                self.session.files_create_folder(dropbox_directory_path, autorename = False)
            
            # Try to remove the directory before making it.  
            elif handle_conflict == 'overwrite':
                try:
                    self.dropbox_directory_remove(dropbox_directory_path, recursive = True)
                except Exception:
                    pass
                self.session.files_create_folder(dropbox_directory_path, autorename = False)

            # Make Directory using the Dropbox autorename procedure
            else:
                self.session.files_create_folder(dropbox_directory_path, autorename = True)
    
    
    def dropbox_directory_download(self, dropbox_directory_path, local_directory_path, 
                                   recursive = False, add_pages = None, overwrite = False):
        '''
        Download a directory and contained files from a Dropbox directory.
        Takes the Dropbox directory and sticks it at the end of local_directory_path.
        Required Arguments:
            dropbox_directory_path: path to a Dropbox directory from root.
            local_directory_path: path to a local directory from the current directory.
        Optional Arguments:
            recursive (boolean): use recursion when creating group of files for download with dropbox_directory_list.
            add_pages (numeric): number of additional pages used by indropbox_directory_list. 
            overwrite (boolean): remove local directory before downloading if it exists and is non-empty.
        '''
        # Get name of new local directory. Use this below.
        download_dropbox_directory_path_extension = os.path.basename(dropbox_directory_path)
        # Append it to the existing local directory path.
        download_dropbox_directory_path = os.path.join(local_directory_path, download_dropbox_directory_path_extension)

        # Check that Dropbox directory exists
        if not self.dropbox_directory_exists(dropbox_directory_path):
            raise Exception('Specified directory does not exist on Dropbox.')

        # Check that a local directory can be overwritten if it is populated.
        elif os.path.isdir(download_dropbox_directory_path) and (os.listdir(download_dropbox_directory_path)) and (overwrite != True):
            raise Exception('Specified directory exists locally and is not empty, but overwrite is not True.')
        
        # Download directory from Dropbox
        else:
            # Make local directory if necessary
            try:
                shutil.rmtree(download_dropbox_directory_path)
            except OSError:
                try:
                    os.makedirs(download_dropbox_directory_path)
                except OSError:
                    raise OSError('Cannot create local directory at specified path')
            
            # Get files and directories for download
            contents = self.dropbox_directory_list(dropbox_directory_path, recursive = recursive, add_pages = add_pages)
            
            # Loop through files and directories for download
            for key in contents:
                for entry in contents[key]:

                    # Get path for download of a file or directory
                    # The tail is everything after the / after the first instace of the dropbox_directory_path in entry. 
                    local_entry_path_tail = entry.path_display.split(dropbox_directory_path, 1)[1][1:]
                    local_entry_path = os.path.join(download_dropbox_directory_path, local_entry_path_tail)
                    
                    # Download files; allow dropbox_file_download to create subdirectories.
                    if type(entry) == dropbox.files.FileMetadata:
                        self.dropbox_file_download(entry.path_display, local_entry_path)
    
    
    def dropbox_directory_upload(self, dropbox_directory_path, local_directory_path, 
                                 recursive = False, overwrite = False): 
        '''
        Upload a directory and contained files to a Dropbox directory.
        Takes the local directory and sticks it at the end of dropbox_directory_path.
        Required Arguments:
            dropbox_directory_path: path to a Dropbox directory from root.
            local_directory_path: path to a local directory from the current directory.
        Optional Arguments:
            recursive (boolean): use recursion when creating group of files for upload.
            add_pages (numeric): number of additional pages used by indropbox_directory_list. 
            overwrite (boolean): remove local directory before downloading if it exists and is non-empty.
        '''
        # Get name of new directory on Dropbox. Use this below.
        upload_dropbox_directory_path_extension = os.path.basename(local_directory_path)
        # Append it to the existing Dropbox directory path.
        upload_dropbox_directory_path = os.path.join(dropbox_directory_path, upload_dropbox_directory_path_extension)

        # Check that recursive argument is properly specified
        if not recursive in [True, False]:
            raise Exception('The recursive argument only accepts True and False')

        # Check that local directory for upload exists
        elif not os.path.isdir(local_directory_path):
            raise Exception('The local directory for upload does not exist.')
        
        # Check that directory on Dropbox can be overwritten if it exists.
        elif (self.dropbox_directory_exists(upload_dropbox_directory_path)) and (overwrite != True):
            raise Exception('The upload location already exists on Dropbox and overwrite is not True')
        
        # Upload directory
        else:
            # Get local files for upload.
            local_file_paths = []
            # If not recursive, only get files at top level of local directory if not recursive.
            if recursive == False:
                for filename in os.listdir(local_directory_path):
                    local_file_path = os.path.join(local_directory_path, filename)
                    if os.path.isfile(local_file_path):
                        local_file_paths.append(local_file_path)
            # If recursive, get files at top level of local directory and in all subdirectories. Don't follow links. 
            else:
                for root, dir, files in os.walk(local_directory_path):
                    for filename in files:
                        local_file_path = os.path.join(root, filename)
                        local_file_paths.append(local_file_path)
            
            # Try to remove the upload directory on Dropbox if overwrite is True.
            if overwrite == True:
                try:
                    self.dropbox_directory_remove(upload_dropbox_directory_path, recursive = True)
                except Exception:
                    pass
            
            # Loop over local files for upload.
            for local_file_path in local_file_paths:
                # Get portion of path to local file after first instance of path to the local directory. 
                local_file_path_extension = local_file_path.split(local_directory_path, 1)[1][1:]
                # Append it to the path to the upload directory on Dropbox
                upload_dropbox_file_path = os.path.join(upload_dropbox_directory_path, local_file_path_extension)
                
                # Upload the local file to Dropbox. 
                # Upload path starts with the upload directory on Dropbox and continues
                # with the part of the path to the local file after the path to the local directory for upload. 
                self.dropbox_file_upload(upload_dropbox_file_path, local_file_path, overwrite = True)
        