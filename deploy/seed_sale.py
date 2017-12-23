import sys

from populus import Project
from utils import (
    deploy_contract,
    dump_abi,
    authority_permit_any,
    check_succesful_tx,
    ensure_working_dir,
    unlock_wallet,
)

working_dir = ensure_working_dir()

def main():
    # Chain must be preconfigured in populus.json
    try:
        _, chain_name, beneficiary = sys.argv
    except ValueError:
        print("Usage:\n python seed_sale.py chain_name beneficiary_address")
        return

    with Project().get_chain(chain_name) as chain:
        web3 = chain.web3
        print("Head block is %d on the %s chain" % (web3.eth.blockNumber, chain_name))

        # The address who will be the owner of the contracts
        owner = web3.eth.coinbase
        if chain_name not in ['tester', 'testrpc']:
            unlock_wallet(chain.web3, owner)

        print('Owner address is', owner)
        print('Beneficiary address is', beneficiary)

        print('Deploying ViewAuthority')
        view_auth = deploy_contract(chain, owner, 'DSGuard')
        print('ViewAuthority address is', view_auth.address)

        print('Deploying ViewToken')
        view_token = deploy_contract(chain, owner, 'DSToken', ['VIEW'])
        print('ViewToken address is', view_token.address)
        tx = view_token.transact().setAuthority(view_auth.address)
        check_succesful_tx(web3, tx)
        print('ViewToken has authorithy set')

        print('Deploying ViewlySeedSale')
        sale = deploy_contract(chain, owner, 'ViewlySeedSale', [view_token.address, beneficiary])
        print('ViewlySeedSale address is', sale.address)
        authority_permit_any(chain, view_auth, sale.address, view_token.address)
        print('ViewlySeedSale is permitted to use ViewToken')

        print(f'Writing ABIs to {working_dir / "build"}')
        dump_abi(view_auth, 'build/view_auth_abi.json')
        dump_abi(view_token, 'build/view_token_abi.json')
        dump_abi(sale, 'build/viewly_seed_sale_abi.json')

        print('All done!')


if __name__ == '__main__':
    main()
