import sys

from populus import Project
from deploy_utils import deploy_contract, dump_abi, authority_permit_any, check_succesful_tx


def main():
    # Chain must be preconfigured in populus.json
    chain_name = sys.argv[1]

    with Project().get_chain(chain_name) as chain:
        web3 = chain.web3
        print("Head block is %d on the %s chain" % (web3.eth.blockNumber, chain_name))

        # The address who will be the owner of the contracts
        owner = web3.eth.coinbase
        print('Owner address is', owner)
        beneficiary = sys.argv[2]
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

        print('Writing ABIs to ./build')
        dump_abi(view_auth, 'build/view_auth_abi.json')
        dump_abi(view_token, 'build/view_token_abi.json')
        dump_abi(sale, 'build/viewly_seed_sale_abi.json')

        print('All done!')


if __name__ == '__main__':
    main()
