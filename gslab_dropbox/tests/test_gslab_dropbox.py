import dropbox
import os
import dbox_class
import shutil
import string
import time
import filecmp

def main(test_directory_name):
    # Instance of gslab_dropbox. All methods accessed as app.COMMAND(ARGS)
    # Access dropbox session as app.session()
    app = dbox_class.gslab_dropbox()
    
    # Make Test directory
    make_test_directory(test_directory_name)
    
    make_test_input(test_directory_name, 'big_file', 10000, 50)
    make_test_input(test_directory_name, 'small_file', 1, make_many = 100)

    for dir in os.listdir(test_directory_name):
        local_test_directory = os.path.join(test_directory_name, dir)
        if os.path.isdir(local_test_directory):
            stats = stats_test_input(local_test_directory)
            dropbox_test_routine(app, '/ARLab Team Folder', test_directory_name, dir, stats)
        else:
            pass


def make_test_directory(test_directory_name):
    try:
        os.makedirs(test_directory_name)
    except:
        input = raw_input('File exists, remove? (y/n)')
        if input == 'y':
            shutil.rmtree(test_directory_name)
        else:
            system.exit()


def make_test_input(test_directory_name, test_name, rep_number, make_many = None):

    subdirectory_one = os.path.join(test_directory_name, test_name)
    os.makedirs(subdirectory_one)
    file_path = '%s/%s.txt' % (subdirectory_one, test_name)
    with open(file_path, 'wb') as f:
        for rep in range(rep_number):
            for char in string.letters:
                f.write((char * rep) + '/n')
    
    if make_many > 0:
        many_test_name = 'many_%ss' % test_name
        subdirectory_many = os.path.join(test_directory_name, many_test_name)
        os.makedirs(subdirectory_many)
        for filenum in range(0, make_many):
            many_file_path = '%s/%s_%s.txt' % (subdirectory_many, many_test_name, filenum)
            shutil.copyfile(file_path, many_file_path) 

 
def stats_test_input(local_test_directory):
    num_files = len([f for f in os.listdir(local_test_directory) if os.path.isfile(os.path.join(local_test_directory, f))])
    size_dir = sum(os.path.getsize(os.path.join(local_test_directory, f)) for f in os.listdir(local_test_directory) 
                   if os.path.isfile(os.path.join(local_test_directory, f)))
    stats = 'of %s bytes with %s files' % (size_dir, num_files)
    return stats


def dropbox_test_routine(app, dropbox_base_path, test_directory_name, dir, dir_stats):
    
    _time_stamp = '_' + str(time.time())
    
    local_upload_test_directory = os.path.join(test_directory_name, dir)
    dropbox_test_directory = os.path.join(dropbox_base_path, test_directory_name + _time_stamp)
    local_download_test_directory = ('.')
    
    print 'Dropbox speed test routine on "%s".' % local_upload_test_directory
    
    # Upload directory
    t_start = time.time()
    app.dropbox_directory_upload(dropbox_test_directory, local_upload_test_directory)
    t_end = time.time()
    t_run = int(t_end - t_start)
    print '  Upload directory %s in %s seconds.' % (dir_stats, t_run)
    
    # Download directory
    t_start = time.time()
    app.dropbox_directory_download(dropbox_test_directory, local_download_test_directory, recursive = True, add_pages = 3)
    t_end = time.time()
    t_run = int(t_end - t_start)
    print '  Download directory %s in %s seconds.' % (dir_stats, t_run)

    # Compare uploaded and downloaded directories
    os.system('diff -r %s %s > comp%s.txt' % 
             (local_upload_test_directory, os.path.join(os.path.basename(dropbox_test_directory), dir), _time_stamp))
    with open('comp%s.txt' % _time_stamp, 'rU') as f:
        lines = f.readlines()
    # Successful if the comparisson file is empty
    if not lines:
        print '  Uploaded and Downloaded files identical. Test Success! Now cleaning up.'
        app.dropbox_directory_remove(dropbox_test_directory, recursive = True)
        os.remove('comp%s.txt' % _time_stamp)
        shutil.rmtree(os.path.basename(dropbox_test_directory))
    else:
        print '  Upload and Download files are not identical. ' 
        print '    See a diff of intended upload and actual download in comp%s.txt. ' % _time_stamp
        print '    See intended upload locally in %s. ' % local_upload_test_directory
        print '    See actual upload on Dropbox in %s. ' % dropbox_test_directory
        print '    See actual Download in %s. ' % os.path.basename(dropbox_test_directory)

main('dbox_test_files')