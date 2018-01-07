from inspect import getsourcefile
from os.path import abspath
from pathlib import Path
import pathlib
import json
import sys
import web3

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

def get_chain(provider: str, chain_name='mainnet', infura_key='') -> web3.Web3:
    """ A convenient wrapper for most common web3 backend sources."""
    from web3 import Web3, HTTPProvider, IPCProvider, TestRPCProvider
    from web3.providers.eth_tester import EthereumTesterProvider
    from eth_tester import EthereumTester

    infura_url = f'https://{chain_name}.infura.io/{infura_key}'
    providers = {
        'tester': lambda: EthereumTesterProvider(EthereumTester()),
        'testrpc': lambda: TestRPCProvider(),
        'http': lambda: HTTPProvider("http://localhost:8545"),
        'parity': lambda: IPCProvider(parity_ipc()),
        'geth': lambda: IPCProvider(geth_ipc(chain_name)),
        'infura': lambda: HTTPProvider(infura_url)
    }
    return Web3(providers[provider]())

def script_source_dir() -> pathlib.Path:
    """ Return the absolute path of *this* python file,
        as its being executed.
    """
    executed_file = Path(abspath(getsourcefile(lambda:0)))
    return executed_file.parent

def load_json(filename):
    with open(filename, 'r') as f:
        return json.loads(f.read())

# --------------------------------------
# Duplicate methods from deploy/utils.py
# --------------------------------------
def unlock_wallet(web3, address):
    from getpass import getpass
    unlocked = False
    while not unlocked:
        pw = getpass(f'Password to unlock {address}: ')
        if not pw:
            break
        unlocked = web3.personal.unlockAccount(address, pw)

def default_wallet_account(web3):
    """
    Returns the coinbase account or the first
    account provided by the wallet.
    """
    if int(web3.eth.coinbase, 16):
        return web3.eth.coinbase

    return web3.eth.accounts[0]

