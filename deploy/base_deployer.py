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
        self.owner = owner or self.web3.eth.coinbase

        if self.chain_name not in ['tester', 'testrpc']:
            unlock_wallet(self.web3, self.owner)
