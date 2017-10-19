from populus.chain.base import BaseChain
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
import json

def load_contract(chain: BaseChain, contract_name, address):
    contract_factory = chain.get_contract_factory(contract_name)
    return contract_factory(address=address)

def deploy_contract(chain: BaseChain, owner, contract_name, args=[]):
    contract_factory = chain.get_contract_factory(contract_name)
    tx = contract_factory.deploy(transaction={"from": owner}, args=args)
    receipt = check_succesful_tx(chain.web3, tx)
    return contract_factory(address=receipt["contractAddress"])

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
    tx = authority.transact().permit(
        src_address,
        dest_address,
        authority.call().ANY()
    )
    return check_succesful_tx(chain.web3, tx)
