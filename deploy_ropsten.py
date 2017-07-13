from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
from eth_utils import to_wei


def check_succesful_tx(web3: Web3, txid: str, timeout=180) -> dict:
    """See if transaction went through (Solidity code did not throw).

    :return: Transaction receipt
    """

    # http://ethereum.stackexchange.com/q/6007/620
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)

    # EVM has only one error mode and it's consume all gas
    assert txinfo["gas"] != receipt["gasUsed"]
    return receipt


def is_running(sale):
    assert sale.call().state() == 1
    return True


def main():
    project = Project()

    # This is configured in populus.json
    # We are working on a testnet
    chain_name = "ropsten"
    with project.get_chain(chain_name) as chain:

        # Load Populus contract proxy classes
        ViewlySale = chain.get_contract_factory('ViewlySale')

        web3 = chain.web3
        print("Web3 provider is", web3.currentProvider)

        # The address who will be the owner of the contracts
        owner = web3.eth.coinbase
        assert owner, "Make sure your node has coinbase account created"
        print("Coinbase address is", owner)

        # Unlock the coinbase account
        web3.personal.unlockAccount(owner, 'test', duration=None)

        # Random address on Ropsten testnet
        # This address will receive ETH funds
        # multisig_address = "0xcbb09f94680f10887f1c358df9aea5c425a1f0b8"
        # print("Multisig address is", multisig_address)

        # Deploy the ViewlySale contract
        txhash = ViewlySale.deploy(
            transaction={"from": owner},
            args=[False]
        )
        print("Deploying crowdsale, tx hash is", txhash)
        receipt = check_succesful_tx(web3, txhash)
        crowdsale_address = receipt["contractAddress"]
        print("ViewlySale contract address is", crowdsale_address)

        # Initialize the sale
        print("Initializing contracts")
        sale = ViewlySale(address=crowdsale_address)
        tx_hash = sale.transact().startSale(
            5 * 24,
            0,
            18_000_000,
            to_wei(18_000_000 // 300, 'ether'),
        )
        check_succesful_tx(web3, tx_hash)

        # state.Running
        assert is_running(sale)

        print("All done! Enjoy your decentralized future.")


if __name__ == "__main__":
    main()
