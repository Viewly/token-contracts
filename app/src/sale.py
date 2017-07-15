from web3 import Web3, IPCProvider

geth_ipc_path = '/Users/user/Library/Ethereum/testnet/geth.ipc'
abi_path = 'build/abi.txt'
owner_address = '0x25b99234a1d2e37fe340e8f9046d0cf0d9558c58'
contract_address = '0x9ff89bb6ff7e6b4a023e8a5c1babccf39d15b75b'

def get_web3():
    web3 = Web3(IPCProvider(geth_ipc_path))

    assert web3.isConnected, "Could not connect to the IPC"
    assert web3.eth.coinbase, "Coinbase account needs to be set"

    return web3

def load_abi(path=abi_path):
    import json
    with open(path, 'r') as f:
        return json.loads(f.read())

def get_contract(address):
    web3 = get_web3()
    # from web3.contract import construct_contract_factory
    # construct_contract_factory(web3=web3)(address=address, abi=load_abi())
    sale = web3.eth.contract(address, abi=load_abi())
    assert sale.address == address, "Contract not found"

    return sale

def unlock_account(address=owner_address, password='test'):
    web3 = get_web3()

    assert web3.personal.unlockAccount(address, password, None), \
        "Could not unlock acccount %s" % address
    return address


def is_running(sale) -> bool:
    acc = unlock_account()
    state = sale.call({"from": acc}).state()
    return state == 1


if __name__ == "__main__":
    sale = get_contract(contract_address)
    print(is_running(sale))
