import click
from populus import Project
from utils import (
    write_json,
    authority_permit_any,
    check_succesful_tx,
    ensure_working_dir,
    confirm_deployment,
)
from base_deployer import BaseDeployer

working_dir = ensure_working_dir()


class SeedSale(BaseDeployer):
    __target__ = 'ViewlySeedSale'

    def __init__(self, chain_name, chain, owner=None, **kwargs):
        """ Initialize the contract.

        Args:
            chain_name: Name of ETH chain (ie. mainnet, ropsten...)
            chain: Populus Project chain instance.
            owner: `from` address to transact with (`msg.sender` in contracts)

        """
        super().__init__(chain_name, chain, owner)

        # multi-contract instances
        self.instances = {
            'DSGuard': kwargs.get('DSGuard'),
            'DSToken': kwargs.get('DSToken'),
            'ViewlySeedSale': kwargs.get('ViewlySeedSale'),
        }


    def deploy(self, beneficiary: str):
        # ViewAuthority
        if not self.instances['DSGuard']:
            self.instances['DSGuard'] = self.deploy_contract('DSGuard')
            print(f"DSGuard address: {self.instances['DSGuard'].address}")

        # ViewToken
        if not self.instances['DSToken']:
            self.instances['DSToken'] = \
                self.deploy_contract('DSToken', args=['VIEW'])

            tx = self.instances['DSToken'] \
                .transact({"from": self.owner}) \
                .setAuthority(self.instances['DSToken'].address)
            check_succesful_tx(self.web3, tx)
            print(f"DSToken address: {self.instances['DSToken'].address}")

        # Seed Sale
        if not self.instances['ViewlySeedSale']:
            self.instances['ViewlySeedSale'] = \
                self.deploy_contract(
                    'ViewlySeedSale',
                    args=[self.instances['DSToken'].address, beneficiary])

            authority_permit_any(
                chain = self.chain,
                authority = self.instances['DSGuard'],
                src_address = self.instances['ViewlySeedSale'].address,
                dest_address = self.instances['DSToken'].address,
            )
            print(f"ViewlySeedSale address: {self.instances['ViewlySeedSale'].address}")

    def deprecate(self):
        pass

    def dump_abis(self):
        print(f'Writing ABIs to {working_dir / "build"}')
        for name, instance in self.instances.items():
            if instance:
                write_json(instance.abi, f'build/{name}.abi.json')


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

        if confirm_deployment(chain_name, deployer.__target__):
            deployer.deploy(beneficiary)
            deployer.dump_abis()

if __name__ == '__main__':
    deploy()
