from web3 import Web3, IPCProvider
from eth_utils import from_wei

geth_ipc_path = '/Users/user/Library/Ethereum/testnet/geth.ipc'

# setup methods
# -------------
def get_web3():
    web3 = Web3(IPCProvider(geth_ipc_path))

    assert web3.isConnected, "Could not connect to the IPC"
    assert web3.eth.coinbase, "Coinbase account needs to be set"

    return web3

def load_abi(path: str):
    import json
    with open(path, 'r') as f:
        return json.loads(f.read())

def get_contract(address: str, abi: list):
    web3 = get_web3()
    # from web3.contract import construct_contract_factory
    # construct_contract_factory(web3=web3)(address=address, abi=load_abi())
    sale = web3.eth.contract(address, abi=abi)
    assert sale.address == address, "Contract not found"

    return sale

def unlock_account(address: str, password: str):
    web3 = get_web3()

    assert web3.personal.unlockAccount(address, password, None), \
        "Could not unlock acccount %s" % address
    return address


class ViewlySale():

    abi_path = 'build/abi.txt'
    owner_address = '0x25b99234a1d2e37fe340e8f9046d0cf0d9558c58'
    contract_address = '0x9ff89bb6ff7e6b4a023e8a5c1babccf39d15b75b'

    def __init__(self, address=None, abi=None, abi_path=None):
        self.address = address or ViewlySale.contract_address
        self.abi = abi or load_abi(abi_path or ViewlySale.abi_path)
        self.sale = get_contract(self.address, self.abi)
        # account that will be calling the contracts
        # this should NOT be the owner in prod
        # self.account = unlock_account()

    def beneficiary(self) -> str:
        return self.sale.call().multisigAddr()

    def current_round_number(self) -> int:
        return self.sale.call().roundNumber()

    def is_running(self) -> bool:
        state = self.sale.call().state()
        return state == 1

    def current_round(self):
        round_number = self.current_round_number()
        return {
            'roundNumber': round_number,
            'roundEthCap': eth_to_int(self.sale.call().roundEthCap()),
            'roundTokenCap': self.sale.call().roundTokenCap(),
            'roundDurationHours': self.sale.call().roundDurationHours(),
            'roundStartBlock': self.sale.call().roundStartBlock(),
            'roundEndBlock': self.sale.call().roundEndBlock(),
            'roundEthRaised': eth_to_int(self.sale.call().mapEthSums(round_number)),
        }

    def deposit_sum_for(self, user, round_number):
        return self.sale.call().mapEthDeposits(round_number, user)

# helpers
# -------
def eth_to_int(amount) -> int:
    return int(from_wei(amount, 'ether'))


if __name__ == "__main__":
    sale = ViewlySale()
    print(sale.is_running())
    print(sale.current_round())
