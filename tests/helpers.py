from web3.contract import Contract
from populus.chain.base import BaseChain

def deploy_contract(chain: BaseChain, contract_name: str, args=[]) -> Contract:
    # deploy contract on chain with coinbase and optional init args
    factory = chain.get_contract_factory(contract_name)
    deploy_tx_hash = factory.deploy(args=args)
    contract_address = chain.wait.for_contract_address(deploy_tx_hash)
    return factory(address=contract_address)

def send_eth(chain, from_address, to_address, eth_to_send):
    return chain.web3.eth.sendTransaction({
        'from': from_address,
        'to': to_address,
        'value': eth_to_send,
        'gas': 250000,
    })
