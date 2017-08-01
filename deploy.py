from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
from eth_utils import to_wei
import json
import sys


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

    # Chain must be preconfigured in populus.json
    chain_name = sys.argv[1]
    with project.get_chain(chain_name) as chain:
        # Load Populus contract proxy classes
        ViewlySale = chain.get_contract_factory('ViewlySale')

        web3 = chain.web3
        print("Head block is %d on the %s chain" \
              % (web3.eth.blockNumber, chain_name))

        # The address who will be the owner of the contracts
        owner = web3.eth.coinbase
        assert owner, "Make sure your node has coinbase account created"
        print("Owner address is", owner)

        # Unlock the coinbase account
        web3.personal.unlockAccount(owner, 'test', duration=None)

        # This address will receive ETH funds when secureEth() is called
        multisig_address = sys.argv[2]
        print("Multisig address is", multisig_address)

        # Deploy the ViewlySale contract
        txhash = ViewlySale.deploy(
            transaction={"from": owner},
            args=[multisig_address, False]
        )
        print("Deploying crowdsale, tx hash is", txhash)
        receipt = check_succesful_tx(web3, txhash)
        crowdsale_address = receipt["contractAddress"]
        print("Contract address is", crowdsale_address)

        # Initialize the sale
        print("Initializing contracts")
        sale = ViewlySale(address=crowdsale_address)
        tx_hash = sale.transact().startSale(
            5 * 24 * 3600 // 17,
            0,
            to_wei(18_000_000, 'ether'),
            to_wei(18_000_000 // 200, 'ether'),
        )
        check_succesful_tx(web3, tx_hash)

        # state.Running
        assert is_running(sale)

        with open('build/abi.txt', 'w') as f:
            f.write(json.dumps(sale.abi))

        print("All done! ABI has been stored in build/abi.txt")


if __name__ == "__main__":
    main()
