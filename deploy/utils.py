from populus.chain.base import BaseChain
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
import json
import os
import pathlib

def ensure_working_dir() -> pathlib.Path:
    """ Ensure that the deployment scripts default to
    the project root as the working dir.
    """
    wd = pathlib.Path.cwd()
    if wd.parts[-1] == 'deploy':
        wd = wd.parent
        os.chdir(wd)
    return wd

def load_contract(chain: BaseChain, contract_name, address):
    contract_factory = chain.provider.get_contract_factory(contract_name)
    return contract_factory(address=address)

def deploy_contract(chain: BaseChain, owner, contract_name, args=[]):
    contract, _ = chain.provider.get_or_deploy_contract(
        contract_name,
        deploy_transaction={'from': owner},
        deploy_args=args,
    )
    return contract

def dump_abi(contract, filename):
    with open(filename, 'w') as f:
        f.write(json.dumps(contract.abi))

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

def authority_permit_any(chain: BaseChain, authority, src_address, dest_address):
    """  Grant *all* priviliges to a specific address or contract via DSGuard proxy.

    Note:
        DSGuard (authority) is authorized to perform actions on the View Token.

    Args:
        chain: base chain
        authority: Address of our DSGuard Proxy.
        src_address:  Contract or address being granted priviliges.
        dest_address: Contract where src_address will get priviliges on.
    """
    tx = authority.transact().permit(
        src_address,
        dest_address,
        authority.call().ANY()
    )
    return check_succesful_tx(chain.web3, tx)
