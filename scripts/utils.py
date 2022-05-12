from sys import argv
import functools
import glob
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data')


def arguments():
    if (len(argv) <= 1):
        print("No collection provided")
        return
    return argv[1:]

def data_files(data, data_path):
    files = []
    for item in data:
        files.extend(glob.glob(os.path.join(data_path,  f'{item}*.json')))
    return files

def args_handler(func):
    @functools.wraps(func)
    def prep_args(*args, **kwargs):
        internal_args = arguments()
        func(internal_args)
    return prep_args
