import click
from populus import Project
from utils import (
    deploy_contract,
    write_json,
    authority_permit_any,
    check_succesful_tx,
    ensure_working_dir,
    unlock_wallet,
)

working_dir = ensure_working_dir()


class SeedSale():
    __target__ = 'ViewlySeedSale'

    def __init__(self, chain_name, chain, owner=None, **kwargs):
        """ Initialize the contract.

        Args:
            chain_name: Name of ETH chain (ie. mainnet, ropsten...)
            chain: Populus Project chain instance.
            owner: `from` address to transact with (`msg.sender` in contracts)

        """
        self.chain_name = chain_name
        assert chain_name in ['mainnet', 'ropsten', 'tester', 'testrpc'], \
                f"Invalid Chain Name {chain_name}"

        self.chain = chain
        self.web3 = self.chain.web3
        self.owner = owner or self.web3.eth.coinbase

        if self.chain_name not in ['tester', 'testrpc']:
            unlock_wallet(self.web3, self.owner)

        # contract instances
        self.instances = {
            'DSGuard': kwargs.get('DSGuard'),
            'DSToken': kwargs.get('DSToken'),
            'ViewlySeedSale': kwargs.get('ViewlySeedSale'),
        }


    def deploy(self, beneficiary: str):
        # ViewAuthority
        if not self.instances['DSGuard']:
            self.instances['DSGuard'] = \
                deploy_contract(self.chain, self.owner, 'DSGuard')
            print(f"DSGuard address: {self.instances['DSGuard'].address}")

        # ViewToken
        if not self.instances['DSToken']:
            self.instances['DSToken'] = \
                deploy_contract(
                    self.chain,
                    self.owner,
                    'DSToken',
                    args=['VIEW'])

            tx = self.instances['DSToken'] \
                .transact({"from": self.owner}) \
                .setAuthority(self.instances['DSToken'].address)
            check_succesful_tx(self.web3, tx)
            print(f"DSToken address: {self.instances['DSToken'].address}")

        # Seed Sale
        if not self.instances['ViewlySeedSale']:
            self.instances['ViewlySeedSale'] = \
                deploy_contract(
                    self.chain,
                    self.owner,
                    'ViewlySeedSale',
                    args=[self.instances['DSToken'].address, beneficiary])

            authority_permit_any(
                chain = self.chain,
                authority = self.instances['DSGuard'],
                src_address = self.instances['ViewlySeedSale'].address,
                dest_address = self.instances['DSToken'].address,
            )
            print(f"ViewlySeedSale address: {self.instances['ViewlySeedSale'].address}")


    def dump_abis(self):
        print(f'Writing ABIs to {working_dir / "build"}')
        for name, instance in self.instances.items():
            if instance:
                write_json(instance.abi, f'build/{name}.abi.json')

def confirm_deployment(chain_name):
    return chain_name != 'mainnet' \
           or click.confirm(f'Deploy {SeedSale.__target__}?')

@click.command()
@click.argument('chain-name', type=str)
@click.argument('beneficiary', type=str)
def deploy(chain_name, beneficiary):
    """ Deploy ViewlySeedSale """
    with Project().get_chain(chain_name) as chain:
        deployer = SeedSale(chain_name, chain)
        print(f'Head block is {deployer.web3.eth.blockNumber} '
              f'on the "{chain_name}" chain')
        print('Owner address is', deployer.owner)
        print('Beneficiary address is', beneficiary)

        if confirm_deployment(chain_name):
            deployer.deploy(beneficiary)
            deployer.dump_abis()

if __name__ == '__main__':
    deploy()
