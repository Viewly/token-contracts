from inspect import getsourcefile
from os.path import abspath
import pathlib
import json

def script_source_dir() -> pathlib.Path:
    """ Return the absolute path of *this* python file,
        as its being executed.
    """
    executed_file = pathlib.Path(abspath(getsourcefile(lambda:0)))
    return executed_file.parent

def load_json(filename):
    with open(filename, 'r') as f:
        return json.loads(f.read())

if __name__  == '__main__':
    print(script_source_dir())
