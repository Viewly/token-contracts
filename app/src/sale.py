from web3 import Web3, KeepAliveRPCProvider

web3 = Web3(KeepAliveRPCProvider(host='localhost', port='7777'))

# from web3.contract import Contract
#
# c = Contract("address")
#
