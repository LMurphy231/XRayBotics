import os
import glob
import importlib.util
import sys
#from api import Robot

def get_lower_files(dir_):
    '''
    Gets all .py files in dir_ and below
    '''
    files = {}
    for file in glob.glob(os.path.join(dir_, '**', '**.py'), recursive=True):
        # Ignore any examples and this file
        if 'example' in file or file == os.path.relpath(__file__, os.getcwd()) or '__init__' in file:
            continue
        if os.path.relpath(os.path.dirname(file), dir_) not in files:
            files[os.path.relpath(os.path.dirname(file), dir_)] = []
        files[os.path.relpath(os.path.dirname(file), dir_)].append(os.path.basename(file))
    return files

def write_init(files, dir_):
    '''
    Write __init__.py in dir_ using .py files in current/sub folders.
    '''
    print(files)
    with open(os.path.join(dir_, '__init__.py'), 'w') as f:
        for folder in files:
            folder_location = folder.replace("\\",".")
            if isinstance(files[folder], (list, tuple)):
                file_list = ", ".join([file.replace('.py','') for file in files[folder]])
            else:
                file_list = files[folder].replace('.py','')

            if folder == dir_ or folder_location == '.' :
                f.write(f'import {file_list}\n')
            else:
                f.write(f'from {folder_location} import {file_list}\n')
        f.write(f'\n\nif __name__ == "__main__":\n    pass')

if __name__ == "__main__":
    folders = []
    

    for dir_ in glob.glob(os.path.join('**'), recursive=True):
        if os.path.splitext(dir_)[1] == '':
            files = get_lower_files(dir_)
            write_init(files, dir_)
    
    # Make current dir_ __init__.py
    files = get_lower_files('')
    write_init(files, '')
    

