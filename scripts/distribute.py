import click
import os
import web3

from web3.utils.validation import validate_address
from toolz import pipe

from utils import load_json
from db import (
    init_db,
    import_txs,
    query_all,
    update_txid,
    mark_tx_as_successful,
    mark_tx_for_retry,
)

roles = 'Founders Supporters Creators Bounties'.split(' ')
buckets = dict(zip(roles, range(len(roles))))

def validated_payouts(payouts_in: dict) -> dict:
    """
    This method validates json transactions.
    It ensures `recipient` addresses are valid ETH addresses,
    and expands `bucket` aliases into proper bucket_id's.
    """
    # swap bucket name with matching ID
    payouts = [
        {**x, 'bucket': buckets[x['bucket'].lower().title()]}
        for x in payouts_in
    ]

    # validate addresses
    _ = [validate_address(x['recipient']) for x in payouts]

    return payouts



def txs_from_json_file(txs_json_path: str) -> dict:
    return pipe(
        txs_json_path,
        load_json,
        validated_payouts,
    )


def get_chain(chain_name: str, infura_key='') -> web3.Web3:
    """ A convenient wrapper for most common web3 backend sources."""
    from web3 import Web3, HTTPProvider, IPCProvider, TestRPCProvider
    from web3.providers.eth_tester import EthereumTesterProvider
    from eth_tester import EthereumTester
    chains = {
        'tester': EthereumTesterProvider(EthereumTester()),
        'testrpc': TestRPCProvider(),
        'testnet': IPCProvider(testnet=True),
        'mainnet': IPCProvider(),
        'infura': HTTPProvider(f'https://mainnet.infura.io/{infura_key}')
    }
    return Web3(chains[chain_name])


def get_mint_tokens_instance(
    abi_path,
    contract_address,
    chain_name='tester', **kwargs) -> web3.eth.Contract:
    """ Reconstruct a contract instance from its address and ABI."""
    abi = load_json(abi_path)
    w3 = get_chain(chain_name, **kwargs)
    return w3.eth.contract(abi, contract_address)


def mint_tokens(
    instance: web3.eth.Contract,
    recipient: str,
    amount: float,
    bucket: int, **kwargs) -> str:
    """ Call `mint` function on target contract.

    Args:
        instance: A MintTokens live contract instance (fully initialized).
        recipient: Address of VIEW Token Recipient.
        amount: Amount of VIEW Tokens to mint.
        bucket: A bucket number of the funding source (Founders, Supporters...)

    Returns:
        txid: Transaction ID of the function call
    """
    assert bucket in buckets, "Invalid bucket id"
    assert type(amount) == float, "Invalid amount type"
    validate_address(recipient)

    tx_props = {
        'value': 0,
    }
    # if gas limit is not provided,
    # w3.eth.estimateGas() is usded
    if 'gas' in kwargs:
        tx_props['gas'] = kwargs['gas']

    # which address we are making a call from
    if 'owner' in kwargs:
        tx_props['from'] = kwargs['owner']

    txid = instance.transact(tx_props).mint(
        recipient, amount, bucket
    )
    return txid

def is_tx_successful(w3: web3.Web3, txid: str) -> bool:
    """ Check whether an Ethereum transaction was successful."""
    receipt = w3.eth.getTransactionReceipt(txid)
    return receipt['blockNumber'] and receipt['status']

def is_tx_out_of_gas(w3: web3.Web3, txid: str) -> bool:
    """ Check whether an Ethereum transaction failed by running out of gas."""
    tx = w3.eth.getTransaction()
    receipt = w3.eth.getTransactionReceipt(txid)
    return receipt['status'] == 0 and tx['gas'] == receipt['gasUsed']

# CLI
# ---
context_settings = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=context_settings)
def cli():
    pass

@cli.command(name='import-txs')
@click.argument('json-file', type=click.Path(exists=True))
@click.argument('db-file', type=click.Path(exists=False))
def cli_import_txs(json_file, db_file):
    """Import transactions from json file to a new database for processing."""
    if os.path.exists(db_file):
        click.confirm(f'Database {db_file} already exists. Overwrite?', abort=True)

    init_db(db_file)
    txs = txs_from_json_file(json_file)
    import_txs(db_file, txs)
    print(f'Imported {len(txs)} transactions into {db_file}')

@cli.command(name='payout')
@click.argument('db-file', type=click.Path(exists=True))
@click.argument('chain-name', type=str)
@click.argument('contract-address', type=str)
@click.argument('contract-abi', type=click.Path(exists=True))
def cli_payout(db_file, chain_name, contract_address, abi_path):
    """Payout pending tx's in the specified database."""

    infura_key = ''
    if chain_name == 'infura':
        infura_key = click.prompt(
            'Please enter your infura key', type=str)

    instance = get_mint_tokens_instance(
        abi_path,
        contract_address,
        chain_name,
        infura_key=infura_key,
    )
    assert instance.address == contract_address

    q = """
    SELECT id, recipient, amount, bucket
     FROM txs
     WHERE txid IS NULL AND success = 0;
    """
    for payout in query_all(db_file, q):
        id_, recipient, amount, bucket = payout
        txid = mint_tokens(
            instance, recipient, amount, bucket,
        )
        update_txid(db_file, id_, txid)


@cli.command(name='verify')
@click.argument('db-file', type=click.Path(exists=True))
@click.argument('chain-name', type=str)
def cli_verify(db_file, chain_name):
    """Verify paid tx's in the specified database."""
    q = """
    SELECT id, txid
     FROM txs
     WHERE success = 0 AND txid IS NOT NULL;
    """
    for id_, txid in query_all(db_file, q):
        if is_tx_successful(txid):
            mark_tx_as_successful(db_file, id_)
        else:
            reason = 'Out of Gas' if is_tx_out_of_gas(txid) else 'Fail'
            if click.confirm(f'{txid} has failed ({reason}). Retry?'):
                mark_tx_for_retry(db_file, id_)


if __name__ == '__main__':
    cli()
