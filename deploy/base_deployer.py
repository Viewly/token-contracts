from utils import (
    unlock_wallet,
)

class BaseDeployer:

    def __init__(self, chain_name, chain, owner=None):
        """ Initialize the deployer.

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

        if owner:
            self.owner = owner
        elif int(self.web3.eth.coinbase, 16):
            self.owner = self.web3.eth.coinbase
        else:
            self.owner = self.web3.eth.accounts[0]

        if self.chain_name not in ['tester', 'testrpc']:
            unlock_wallet(self.web3, self.owner)

    def deploy_contract(self, contract_name, args=[], **kwargs):
        tx_props = {'from': self.owner}
        if 'gas' in kwargs:
            tx_props['gas'] = kwargs['gas']

        contract, _ = self.chain.provider.get_or_deploy_contract(
            contract_name,
            deploy_transaction=tx_props,
            deploy_args=args,
        )
        return contract
