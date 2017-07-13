from web3 import Web3, IPCProvider

geth_ipc_path = '/Users/user/Library/Ethereum/testnet/geth.ipc'

def get_web3():
    web3 = Web3(IPCProvider(geth_ipc_path))

    assert web3.isConnected, "Could not connect to the IPC"
    assert web3.eth.coinbase, "Coinbase account needs to be set"

    return web3

def get_contract(address):
    web3 = get_web3()

    # TODO: this won't work,
    # as we are missing the abi
    # https://github.com/pipermerriam/web3.py/blob/master/web3/contract.py#L882
    sale = web3.eth.contract(address)
    assert sale.address == address, "Contract not found"

    return sale

def unlock_account():
    address = "0x25b99234a1d2e37fe340e8f9046d0cf0d9558c58"
    web3 = get_web3()

    assert web3.personal.unlockAccount(address, 'test', None), \
        "Could not unlock acc"
    return address


def is_running(sale) -> bool:
    acc = unlock_account()
    state = sale.call({"from": acc}).state()
    return state == 1


if __name__ == "__main__":
    sale = get_contract("0x9ff89bb6ff7e6b4a023e8a5c1babccf39d15b75b")
    # print(is_running(sale))
