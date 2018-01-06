from inspect import getsourcefile
from os.path import abspath
from pathlib import Path
import pathlib
import json
import sys

def geth_ipc(chain_name: str) -> str:
    """ Get the geth IPC path for any chain.

    Args:
        chain_name: mainnet, rinkeby, ropsten, kovan, etc...
    """

    if sys.platform == 'darwin':
        geth_path  = 'Library/Ethereum'
    elif sys.platform.startswith('linux'):
        geth_path  = '.ethereum'

    if chain_name == 'mainnet':
        chain_name = ''

    return str(Path.home() / geth_path / chain_name / 'geth.ipc')

def parity_ipc() -> str:
    """ Get the parity IPC path for any chain. """

    if sys.platform == 'darwin':
        parity_path  = 'Library/Application Support/io.parity.ethereum'
    elif sys.platform.startswith('linux'):
        parity_path  = '.local/share/io.parity.ethereum'

    return str(Path.home() / parity_path / 'jsonrpc.ipc')

def script_source_dir() -> pathlib.Path:
    """ Return the absolute path of *this* python file,
        as its being executed.
    """
    executed_file = Path(abspath(getsourcefile(lambda:0)))
    return executed_file.parent

def load_json(filename):
    with open(filename, 'r') as f:
        return json.loads(f.read())

if __name__  == '__main__':
    print(script_source_dir())
