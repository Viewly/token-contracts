from populus.chain.base import BaseChain
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
import json
import os
import pathlib
import click

def ensure_working_dir() -> pathlib.Path:
    """ Ensure that the deployment scripts default to
    the project root as the working dir.
    """
    wd = pathlib.Path.cwd()
    if wd.parts[-1] == 'deploy':
        wd = wd.parent
        os.chdir(wd)
    return wd

def write_json(data, filename):
    with open(filename, 'w') as f:
        f.write(json.dumps(data, indent=2))

def load_contract(chain: BaseChain, contract_name, address):
    contract_factory = chain.provider.get_contract_factory(contract_name)
    return contract_factory(address=address)

def check_succesful_tx(web3: Web3, txid: str, timeout=600) -> dict:

    """See if transaction went through (Solidity code did not throw).

    :return: Transaction receipt
    """

    # http://ethereum.stackexchange.com/q/6007/620
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)

    # EVM has only one error mode and it's consume all gas
    assert txinfo["gas"] != receipt["gasUsed"]
    return receipt

def unlock_wallet(web3, address):
    from getpass import getpass
    unlocked = False
    while not unlocked:
        pw = getpass(f'Password to unlock {address}: ')
        if not pw:
            break
        unlocked = web3.personal.unlockAccount(address, pw)

def confirm_deployment(chain_name, deploy_target):
    return chain_name != 'mainnet' \
           or click.confirm(f'Deploy {deploy_target}?')
