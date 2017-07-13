from populus import Project
project = Project()

with project.get_chain('ropsten') as chain:
    print('coinbase:', chain.web3.eth.coinbase)
