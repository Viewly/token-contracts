import click
import stringcase
from populus import Project
from utils import (
    load_contract,
    write_json,
    ensure_working_dir,
    confirm_deployment,
)
from base_deployer import BaseDeployer

working_dir = ensure_working_dir()

class TokenMintage(BaseDeployer):
    __target__ = 'ViewTokenMintage'
    __dependencies__ = ['ViewAuthority', 'ViewToken']

    def __init__(self,
                 chain_name,
                 chain,
                 owner=None,
                 instance=None,
                 **kwargs):
        """ Initialize the deployer.

        Args:
            chain_name: Name of ETH chain (ie. mainnet, ropsten...)
            chain: Populus Project chain instance.
            owner: `from` address to transact with (`msg.sender` in contracts)
            instance: A fully loaded instance of this contract.
        """
        super().__init__(chain_name, chain, owner)

        # contract instances
        self.instance = instance

        self.dependencies = {
            'ViewToken': kwargs.get('ViewToken'),
            'ViewAuthority': kwargs.get('ViewAuthority'),
        }


    def deploy(self):
        """ Deploy this contract and perform setup."""
        if self.instance:
            raise ValueError(f"Instance already deployed at {self.instance.address}")

        self.instance = self.deploy_contract(
            contract_name='ViewTokenMintage',
            args=[self.dependencies['ViewToken'].address])
        print(f'{self.__target__} address is', self.instance.address)

        self.authority_permit_any(
            authority=self.dependencies['ViewAuthority'],
            src_address=self.instance.address,
            dst_address=self.dependencies['ViewToken'].address)

    def deprecate(self):
        """ Destroy this contract, and clean up."""
        if not self.instance:
            raise ValueError('Cannot deprecate a non-existing instance')

        # TODO:
        # - call suicide() on contract
        # - remove the contract from authority

    def dump_abis(self):
        print(f'Writing ABIs to {working_dir / "build"}')
        write_json(
            self.instance.abi,
            f'build/{stringcase.snakecase(self.__target__)}.abi.json')


@click.command()
@click.option('--chain', 'chain_name', default='tester',
              type=str, help='Name of ETH Chain')
@click.option('--owner', default=None,
              type=str, help='Account to deploy from')
@click.argument('view-authority-addr', type=str)
@click.argument('view-token-addr', type=str)
def deploy(chain_name, owner, view_authority_addr, view_token_addr):
    """ Deploy ViewTokenMintage """
    with Project().get_chain(chain_name) as chain:
        view_token = load_contract(chain, 'DSToken', view_token_addr)
        view_authority = load_contract(chain, 'DSGuard', view_authority_addr)
        deps = {
            'ViewAuthority': view_authority,
            'ViewToken': view_token,
        }
        deployer = TokenMintage(chain_name, chain, owner=owner, **deps)
        print(f'Head block is {deployer.web3.eth.blockNumber} '
              f'on the "{chain_name}" chain')
        print('Owner address is', deployer.owner)
        print('ViewAuthority address is', view_authority.address)
        print('ViewToken address is', view_token.address)

        if confirm_deployment(chain_name, deployer.__target__):
            deployer.deploy()
            deployer.dump_abis()


if __name__ == '__main__':
    deploy()
