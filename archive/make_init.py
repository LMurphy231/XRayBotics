import os
import glob
import importlib.util
import sys
#from api.farinoAPI.fairino import Robot
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
        key = os.path.relpath(os.path.dirname(file), dir_) if dir_ != '' else os.path.dirname(file).split('\\')[0]
        #print((os.path.dirname(file), dir_))
        if key not in files:
            files[key] = []
        files[key].append(os.path.basename(file))
    return files

def write_init(files, dir_):
    '''
    Write __init__.py in dir_ using .py files in current/sub folders.
    '''
    print(files)
    with open(os.path.join(dir_, '__init__.py'), 'w') as f:
        #f.write(f'import os, sys\n')
        #f.write(f'sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))\n\n')
        #for folder in files:
        #    folder_location = folder.split('\\')[0].replace("\\",".")
        #    
        #    if isinstance(files[folder], (list, tuple)):
        #        file_list = ", ".join([file.replace('.py','') for file in files[folder]])
        #    else:
        #        file_list = files[folder].replace('.py','')
        #    print((os.path.join(dir_, '__init__.py'), folder, folder_location, dir_, file_list))
        #    if folder == dir_ or folder_location == '.' :
        #        
        #        #f.write(f'try:\n    import {file_list}\nexcept:\n    from . import {file_list}\n')
        #        pass
        #    else:
        #        f.write(f'try:\n    from {folder_location} import {file_list}\nexcept:\n    from . import {file_list}\n')
        #        #f.write(f'from {folder_location} import {file_list}\n')
        f.write(f'\n\nif __name__ == "__main__":\n    pass')
        pass

if __name__ == "__main__":
    folders = []
    

    for dir_ in glob.glob(os.path.join('**'), recursive=True):
        if os.path.splitext(dir_)[1] == '':
            files = get_lower_files(dir_)
            write_init(files, dir_)
    
    # Make current dir_ __init__.py
    files = get_lower_files('')
    write_init(files, '')
    

