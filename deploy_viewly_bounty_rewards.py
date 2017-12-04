import sys

from populus import Project
from deploy_utils import (
    load_contract,
    deploy_contract,
    dump_abi,
    authority_permit_any,
)


def main():
    try:
        _, chain_name, view_token_addr, view_auth_addr, *_ = sys.argv
    except ValueError:
        print("Usage:\n python deploy.py "
              "chain_name view_token_addr view_auth_addr")
        return

    with Project().get_chain(chain_name) as chain:
        print("Head block is %d on the %s chain" % (chain.web3.eth.blockNumber, chain_name))

        owner = chain.web3.eth.coinbase
        view_token = load_contract(chain, 'DSToken', view_token_addr)
        view_auth = load_contract(chain, 'DSGuard', view_auth_addr)
        print('Owner address is', owner)
        print('ViewToken address is', view_token.address)
        print('ViewAuthorithy address is', view_auth.address)

        print('Deploying ViewlyBountyRewards')
        bounty = deploy_contract(chain, owner, 'ViewlyBountyRewards', [view_token.address])
        print('ViewlyBountyRewards address is', bounty.address)

        authority_permit_any(chain, view_auth, bounty.address, view_token.address)
        print('ViewlyBountyRewards is permitted to use ViewToken')

        print('Writing ABIs to ./build')
        dump_abi(bounty, 'build/viewly_bounty_rewards.json')

        print('All done!')


if __name__ == '__main__':
    main()
