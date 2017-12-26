import sys

from populus import Project
from utils import (
    load_contract,
    deploy_contract,
    dump_abi,
    authority_permit_any,
    ensure_working_dir,
    unlock_wallet,
)

working_dir = ensure_working_dir()

contract_name = 'MintTokens'

def main():
    try:
        _, chain_name, view_token_addr, view_auth_addr = sys.argv
    except ValueError:
        print("Usage:\n python mint_tokens.py "
              "chain_name view_token_addr view_auth_addr")
        return

    with Project().get_chain(chain_name) as chain:
        print(f"Head block is {chain.web3.eth.blockNumber} "
              f"on the {chain_name} chain")

        owner = chain.web3.eth.coinbase
        if chain_name not in ['tester', 'testrpc']:
            unlock_wallet(chain.web3, owner)

        view_token = load_contract(chain, 'DSToken', view_token_addr)
        view_auth = load_contract(chain, 'DSGuard', view_auth_addr)
        print('Owner address is', owner)
        print('ViewToken address is', view_token.address)
        print('ViewAuthorithy address is', view_auth.address)

        print(f'Deploying {contract_name}.sol')
        mint_tokens = deploy_contract(
            chain=chain,
            owner=owner,
            contract_name=contract_name,
            args=[view_token.address])
        print(f'{contract_name} address is', mint_tokens.address)

        authority_permit_any(
            chain=chain,
            authority=view_auth,
            src_address=mint_tokens.address,
            dest_address=view_token.address)
        print(f'{contract_name} is permitted to use ViewToken')

        print(f'Writing ABIs to {working_dir / "build"}')
        dump_abi(mint_tokens, f'build/{contract_name}.json')

        print('All done!')


if __name__ == '__main__':
    main()
