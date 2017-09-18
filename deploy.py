from populus import Project
from populus.chain.base import BaseChain
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
import json
import sys


def main():
    # Chain must be preconfigured in populus.json
    chain_name = sys.argv[1]

    with Project().get_chain(chain_name) as chain:
        web3 = chain.web3
        print("Head block is %d on the %s chain" % (web3.eth.blockNumber, chain_name))

        # The address who will be the owner of the contracts
        owner = web3.eth.coinbase

        print('Owner address is', owner)

        # Unlock the coinbase account
        web3.personal.unlockAccount(owner, 'test', duration=None)

        print('Deploying ViewAuthority')
        view_auth = deploy_contract(chain, owner, 'DSGuard')
        print('ViewAuthority address is', view_auth.address)

        print('Deploying ViewToken')
        view_token = deploy_contract(chain, owner, 'DSToken', ['VIEW'])
        print('ViewToken address is', view_token.address)
        tx = view_token.transact().setAuthority(view_auth.address)
        check_succesful_tx(web3, tx)
        print('ViewToken has authorithy set')

        print('Deploying ViewlySale')
        multisig_address = sys.argv[2]
        sale = deploy_contract(chain, owner, 'ViewlySale', [view_token.address, multisig_address])
        print('ViewlySale address is', sale.address)
        authority_permit_any(chain, view_auth, sale.address, view_token.address)
        print('ViewlySale is permitted to use ViewToken')

        print('Writing ABIs to ./build')
        dump_abi(view_auth, 'build/view_auth_abi.json')
        dump_abi(view_token, 'build/view_token_abi.json')
        dump_abi(sale, 'build/viewly_sale_abi.json')

        print('All done!')


def check_succesful_tx(web3: Web3, txid: str, timeout=180) -> dict:
    """See if transaction went through (Solidity code did not throw).

    :return: Transaction receipt
    """

    # http://ethereum.stackexchange.com/q/6007/620
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)

    # EVM has only one error mode and it's consume all gas
    assert txinfo["gas"] != receipt["gasUsed"]
    return receipt

def deploy_contract(chain: BaseChain, owner, contract_name, args=[]):
    contract_factory = chain.get_contract_factory(contract_name)
    tx = contract_factory.deploy(transaction={"from": owner}, args=args)
    receipt = check_succesful_tx(chain.web3, tx)
    return contract_factory(address=receipt["contractAddress"])

def authority_permit_any(chain: BaseChain, authority, src_address, dest_address):
    tx = authority.transact().permit(
        src_address,
        dest_address,
        authority.call().ANY()
    )
    return check_succesful_tx(chain.web3, tx)

def dump_abi(contract, filename):
    with open(filename, 'w') as f:
        f.write(json.dumps(contract.abi))

if __name__ == '__main__':
    main()
