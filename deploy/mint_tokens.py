import click
from populus import Project
from utils import (
    load_contract,
    write_json,
    authority_permit_any,
    ensure_working_dir,
    confirm_deployment,
)
from base_deployer import BaseDeployer

working_dir = ensure_working_dir()

class MintTokens(BaseDeployer):
    __target__ = 'MintTokens'
    __dependencies__ = ['DSGuard', 'DSToken']

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
            'DSToken': kwargs.get('DSToken'),
            'DSGuard': kwargs.get('DSGuard'),
        }


    def deploy(self):
        """ Deploy this contract and perform setup."""
        if self.instance:
            raise ValueError(f"Instance already deployed at {self.instance.address}")

        self.instance = self.deploy_contract(
            contract_name='MintTokens',
            args=[self.dependencies['DSToken'].address])
        print(f'{self.__target__} address is', self.instance.address)

        authority_permit_any(
            chain=self.chain,
            authority=self.dependencies['DSGuard'],
            src_address=self.instance.address,
            dest_address=self.dependencies['DSToken'].address)

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
            f'build/{self.__target__}.abi.json')


@click.command()
@click.argument('chain-name', type=str)
@click.argument('ds-token-addr', type=str)
@click.argument('ds-guard-addr', type=str)
def deploy(chain_name, ds_token_addr, ds_guard_addr):
    """ Deploy MintTokens """
    with Project().get_chain(chain_name) as chain:
        ds_token = load_contract(chain, 'DSToken', ds_token_addr)
        ds_guard = load_contract(chain, 'DSGuard', ds_guard_addr)
        deps = {
            'DSGuard': ds_guard,
            'DSToken': ds_guard,
        }
        deployer = MintTokens(chain_name, chain, **deps)
        print(f'Head block is {deployer.web3.eth.blockNumber} '
              f'on the "{chain_name}" chain')
        print('Owner address is', deployer.owner)
        print('ViewToken address is', ds_token.address)
        print('ViewAuthorithy address is', ds_guard.address)

        if confirm_deployment(chain_name, deployer.__target__):
            deployer.deploy()
            deployer.dump_abis()


if __name__ == '__main__':
    deploy()
