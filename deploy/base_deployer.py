from utils import (
    unlock_wallet,
    check_succesful_tx,
    default_wallet_account,
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
        self.owner = owner or default_wallet_account(self.web3)

        if self.chain_name not in ['tester', 'testrpc']:
            unlock_wallet(self.web3, self.owner)

    def deploy_contract(self, contract_name, args=[], **kwargs):
        tx_props = {'from': self.owner}
        if 'gas' in kwargs:
            tx_props['gas'] = kwargs['gas']

        contract, _ = self.chain.provider.deploy_contract(
            contract_name,
            deploy_transaction=tx_props,
            deploy_args=args,
        )
        return contract

    def authority_permit_any(self, authority, src_address, dst_address):
        """  Grant *all* priviliges to a specific address or contract via DSGuard proxy.

        Note:
            DSGuard (authority) is authorized to perform actions on the View Token.

        Args:
            authority: Address of our DSGuard Proxy.
            src_address:  Contract or address being granted priviliges.
            dest_address: Contract where src_address will get priviliges on.
        """
        tx_props = {'from': self.owner}
        tx = authority.transact(tx_props).permit(
            src_address,
            dst_address,
            authority.call().ANY()
        )
        return check_succesful_tx(self.web3, tx)
