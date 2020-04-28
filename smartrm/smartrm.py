#!/usr/bin/python3.8
# -*- coding: utf-8 -*-

import argparse
import os
import datetime
import json
import logging


# get file or directory size
def get_size(path):
    module_logger.debug('Get file or directory size')
    if os.path.isdir(path):
        amount = 0
        for dir, _, files in os.walk(path):
            for fn in files:
                amount += os.path.getsize(os.path.join(dir, fn))
        return amount
    else:
        return os.path.getsize(path)


# convert file or directory size
def _convert(size):
    module_logger.debug('Convert file or directory size')
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    for x in units:
        if size < 1024.0:
            return f"{size:.1f}{x}"
        size = size / 1024.0


# checking the existence of a file or directory
def _file_exists(func):
    def inner(obj, *args):
        module_logger.debug('Checking the existence of a file or directory')
        file_name, *args = args
        new_path = os.path.abspath(file_name)
        if not os.path.exists(new_path):
            return module_logger.error(f'No such file or directory: {new_path}')
        if not os.access(new_path, os.W_OK):
            raise FileExistsError(f'No access to change file {new_path}')
        result = func(obj, new_path, *args)
        return result
    return inner


class File:
    def __init__(self, removal_path, new_trash_path):
        self.name = os.path.basename(removal_path)
        self.size = get_size(removal_path)
        self.new_trash_path = new_trash_path
        self.removal_path = os.path.split(removal_path)[0]
        self.removal_time = datetime.datetime.now().strftime("%d.%m.%Y,%H:%M:%S")
        if os.path.isdir(removal_path):
            self.type = 'folder'
        else:
            self.type = 'file'

    def info(self):
        file_info = {
            'name': self.name,
            'removal_path': self.removal_path,
            'removal_time': self.removal_time,
            'size': _convert(self.size),
            'type': self.type
        }
        return file_info


class SmartRM:
    ACCESS_RIGHTS = 0o777

    def __init__(self):
        if not os.path.exists('Rubbish'):
            os.mkdir(os.path.abspath('Rubbish'))
            self.trash_path = os.path.abspath('Rubbish')
            os.chmod(self.trash_path, self.ACCESS_RIGHTS)
            module_logger.debug(f'Create rubbish can on {self.trash_path}')
            module_logger.info(f'Created Rubbish can on {self.trash_path}')
        self.trash_path = os.path.abspath('Rubbish')
        self.debug_flag = False

    # show path of rubbish can
    def path_of_trash_can(self):
        if not os.path.exists(self.trash_path):
            module_logger.error('Rubbish can not found')
        module_logger.info(f'Path of rubbish can: {self.trash_path}')

    def _save_info(self, rubbish):
        module_logger.debug('Save info about file')
        json_path = os.path.join(self.trash_path, 'trash_info.json')
        data = {}
        if os.path.exists(json_path):
            with open(json_path, 'r') as json_file:
                if not os.path.getsize(json_path) == 0:
                    data.update(json.load(json_file))
        with open(json_path, 'w') as json_file:
            data[rubbish.name] = rubbish.info()
            json.dump(data, json_file)

    def _load_info(self):
        module_logger.debug('Load information')
        json_path = os.path.join(self.trash_path, 'trash_info.json')
        data = {}
        if os.path.exists(json_path):
            with open(json_path, 'r') as file:
                if not os.path.getsize(json_path) == 0:
                    data.update(json.load(file))
                return data
        else:
            module_logger.error('trash_info.json not found')

    def return_info(self):
        module_logger.debug('Garbage output')
        trash_path = os.path.join(self.trash_path, 'trash_info.json')
        if not os.path.exists(trash_path):
            raise FileNotFoundError(f'No such file or directory: {trash_path}')

        print_info = (f"\n\t\t\t\t\033[33m◄\033[36m information \033[33m►\n" + f'\033[33m_' * 75 + '\n'
                      f"\033[36m{'         name of file':31}\033[33m|\033[36m{'   type':10}\033[33m|"
                      f"\033[36m{'   size':10}\033[33m|\033[36m{'    removal time':11}"
                      f"\n" + f'\033[33m‾' * 75 + '\n')
        with open(trash_path) as file:
            json_file = json.load(file)
            if json_file == {}:
                print_info += f"\t\t\t\t   \033[96m{'is empty'}\n"
            else:
                for files in json_file:
                    info = json_file[files]
                    print_info += (f"\033[96m{info['name']:30} \033[33m| "
                                   f"\033[33m  {info['type']:6} \033[33m|"
                                   f"\033[96m {info['size']:8} \033[33m| "
                                   f"\033[96m{info['removal_time']:10} \033[00m\n")
            print_info += f'\033[33m‾' * 75 + '\n'
        return print_info

    @_file_exists
    def delete(self, path):
        module_logger.debug('Start of deletion')
        all_space = os.statvfs(self.trash_path).f_bfree
        new_trash_path = os.path.join(self.trash_path, os.path.basename(path))
        trash = File(path, new_trash_path)
        if all_space < trash.size:
            module_logger.error('No free disk space')
        self._mov(path, self.trash_path)
        self._save_info(trash)
        module_logger.info('File has been deleted')

    def restore(self, name_file):
        module_logger.debug('Start of restoring')
        data = self._load_info()
        if data and name_file in data:
            new_data = data.pop(name_file)
            save_path = os.path.join(self.trash_path, 'trash_info.json')
            with open(save_path, 'w') as file:
                json.dump(data, file)
            path_to_restore = new_data['removal_path']
            path_of_file = os.path.join(self.trash_path, name_file)
            self._mov(path_of_file, path_to_restore)
            module_logger.debug(f'Updated information of trash')
            json_path = os.path.join(self.trash_path, 'trash_info.json')
            with open(json_path, 'w') as file:
                json.dump(data, file)
            module_logger.info(f'File restored: {name_file}')
        else:
            module_logger.error(f'No such file or directory: {name_file}')

    def remove(self, name_file):
        module_logger.debug('Start of removing')
        trash_path = os.path.join(self.trash_path, name_file)
        data = self._load_info()
        if data and name_file in data:
            self._rem_forever(trash_path)
            data.pop(name_file)
            module_logger.debug(f'Updated information of trash')
            json_path = os.path.join(self.trash_path, 'trash_info.json')
            with open(json_path, 'w') as file:
                json.dump(data, file)
            module_logger.info(f'File removed: {name_file}')
        else:
            module_logger.error(f'No such file or directory: {name_file}')

    def clear(self):
        module_logger.debug('Start clearing')
        file_list = os.listdir(self.trash_path)
        data = {}
        for file in file_list:
            if file == 'trash_info.json':
                continue
            self.remove(file)
        module_logger.debug(f'Updated information of trash')
        json_path = os.path.join(self.trash_path, 'trash_info.json')
        with open(json_path, 'w') as file:
            json.dump(data, file)
        module_logger.info('Cleared')

    @_file_exists
    def _mov(self, file, path):
        if os.path.isdir(file):
            new_dir = os.path.join(path, os.path.basename(file))
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            for el in os.listdir(file):
                file_path = os.path.join(file, el)
                self._mov(file_path, new_dir)
            os.rmdir(file)
        else:
            new_file_path = os.path.join(path, os.path.basename(file))
            os.replace(file, new_file_path)

    @_file_exists
    def _rem_forever(self, file):
        if os.path.isdir(file):
            list_of_files = os.listdir(file)
            for el in list_of_files:
                file_path = os.path.join(file, el)
                self._rem_forever(file_path)
            os.rmdir(file)
        else:
            os.remove(file)


logger = logging.getLogger('SmartRM')
console_handler = logging.StreamHandler()

console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
console_handler.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

if __name__ == '__main__':
    module_logger = logging.getLogger('SmartRM')

    parser = argparse.ArgumentParser(prog='SmartRM', description='File removal and recovery utility')
    parser.add_argument('path', type=str, nargs='?', help='Path of file (required)')
    args_group = parser.add_mutually_exclusive_group(required=True)
    args_group.add_argument('-d', '--delete', action='store_true', help='Delete file to trash')
    args_group.add_argument('-rs', '--restore', action='store_true', help='Restore file from trash')
    args_group.add_argument('-rm', '--remove', action='store_true', help='Permanently delete file from trash')
    args_group.add_argument('-c', '--clear', action='store_true', help='Permanently delete all files from trash')
    args_group.add_argument('-i', '--info', action='store_true', help='Show all files in trash')
    args_group.add_argument('-t', '--trash', action='store_true', help='Show path of rubbish can')

    args = parser.parse_args()

    rubbish = SmartRM()

    if args.delete:
        rubbish.delete(args.path)
    elif args.restore:
        rubbish.restore(args.path)
    elif args.remove:
        rubbish.remove(args.path)
    elif args.clear:
        rubbish.clear()
    elif args.info:
        print(rubbish.return_info())
    elif args.trash:
        rubbish.path_of_trash_can()
