from populus import Project
project = Project()

with project.get_chain('ropsten') as chain:
    print('coinbase:', chain.web3.eth.coinbase)

    ViewlySale = chain.get_contract_factory('ViewlySale')
    sale = ViewlySale(address="0x9ff89bb6ff7e6b4a023e8a5c1babccf39d15b75b")
    print(sale.abi)


    print("Sale is running:", sale.call().state() == 1)
