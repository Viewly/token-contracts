import click
import stringcase
from populus import Project
from utils import (
    write_json,
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
            'ViewAuthority': kwargs.get('ViewAuthority'),
            'ViewToken': kwargs.get('ViewToken'),
            'ViewlySeedSale': kwargs.get('ViewlySeedSale'),
        }


    def deploy(self, beneficiary: str):
        # ViewAuthority
        if not self.instances['ViewAuthority']:
            self.instances['ViewAuthority'] = \
                self.deploy_contract('DSGuard', gas=1_340_000)
            print(f"ViewAuthority address: {self.instances['ViewAuthority'].address}")

        # ViewToken
        if not self.instances['ViewToken']:
            self.instances['ViewToken'] = \
                self.deploy_contract('DSToken', args=['VIEW'], gas=2_000_000)

            tx = self.instances['ViewToken'] \
                .transact({"from": self.owner}) \
                .setAuthority(self.instances['ViewAuthority'].address)
            check_succesful_tx(self.web3, tx)
            print(f"ViewToken address: {self.instances['ViewToken'].address}")

        # Seed Sale
        if not self.instances['ViewlySeedSale']:
            self.instances['ViewlySeedSale'] = \
                self.deploy_contract(
                    'ViewlySeedSale',
                    args=[self.instances['ViewToken'].address, beneficiary])

            self.authority_permit_any(
                authority = self.instances['ViewAuthority'],
                src_address = self.instances['ViewlySeedSale'].address,
                dst_address = self.instances['ViewToken'].address,
            )
            print(f"ViewlySeedSale address: {self.instances['ViewlySeedSale'].address}")

    def deprecate(self):
        pass

    def dump_abis(self):
        print(f'Writing ABIs to {working_dir / "build"}')
        for name, instance in self.instances.items():
            if instance:
                abi_file = f'{stringcase.snakecase(name)}.abi.json'
                write_json(instance.abi, f'build/{abi_file}')


@click.command()
@click.option('--chain', 'chain_name', default='tester',
              type=str, help='Name of ETH Chain')
@click.option('--owner', default=None,
              type=str, help='Account to deploy from')
@click.argument('beneficiary', type=str)
def deploy(chain_name, owner, beneficiary):
    """ Deploy ViewlySeedSale """
    with Project().get_chain(chain_name) as chain:
        deployer = SeedSale(chain_name, chain, owner=owner)
        print(f'Head block is {deployer.web3.eth.blockNumber} '
              f'on the "{chain_name}" chain')
        print('Owner address is', deployer.owner)
        print('Beneficiary address is', beneficiary)

        if confirm_deployment(chain_name, deployer.__target__):
            deployer.deploy(beneficiary)
            deployer.dump_abis()

if __name__ == '__main__':
    deploy()
