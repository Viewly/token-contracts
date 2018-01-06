import click
import os
import web3

from web3.utils.validation import validate_address
from toolz import pipe
from eth_utils import to_wei

from utils import load_json, get_chain
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


def get_mint_tokens_instance(
    w3: web3.Web3,
    abi_path: str,
    contract_address: str) -> web3.eth.Contract:
    """ Reconstruct a contract instance from its address and ABI."""
    abi = load_json(abi_path)
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
    assert bucket in buckets.values(), "Invalid bucket id"
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
    if kwargs.get('owner'):
        tx_props['from'] = kwargs['owner']
    else:
        # we could fallback to coinbase in future,
        # however for now its explicit
        raise ValueError('Missing the address to send transaction from. '
                         'Try using the --owner flag')

    txid = instance.transact(tx_props).mint(
        recipient,
        to_wei(amount, 'ether'),
        bucket
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
@click.option('--provider', 'chain_provider', default='tester', type=str,
              help='Chain Provider (parity, geth, tester...)')
@click.option('--chain', 'chain_name', default='mainnet', type=str,
              help='Name of ETH Chain (mainnet, kovan, rinkeby...)')
@click.option('--owner', default=None, type=str,
              help='Account to call the contract from')
@click.argument('db-file', type=click.Path(exists=True))
@click.argument('contract-address', type=str)
@click.argument('abi-path', type=click.Path(exists=True))
def cli_payout(chain_provider, chain_name, owner, db_file, contract_address, abi_path):
    """Payout pending tx's in the specified database."""

    infura_key = ''
    if chain_provider == 'infura':
        infura_key = click.prompt(
            'Please enter your infura key', type=str)

    w3 = get_chain(chain_provider, chain_name, infura_key=infura_key)
    instance = get_mint_tokens_instance(w3, abi_path, contract_address)
    assert instance.address.lower() == contract_address.lower()

    q = """
    SELECT id, recipient, amount, bucket
     FROM txs
     WHERE txid IS NULL AND success = 0;
    """
    for payout in query_all(db_file, q):
        id_, recipient, amount, bucket = payout
        txid = mint_tokens(
            instance, recipient, amount, bucket, owner=owner,
        )
        update_txid(db_file, id_, txid)
        print(f'Minted {amount} tokens to {recipient}')


@cli.command(name='verify')
@click.option('--provider', 'chain_provider', default='tester', type=str,
              help='Chain Provider (parity, geth, tester...)')
@click.option('--chain', 'chain_name', default='mainnet', type=str,
              help='Name of ETH Chain (mainnet, kovan, rinkeby...)')
@click.argument('db-file', type=click.Path(exists=True))
def cli_verify(chain_provider, chain_name, db_file):
    """Verify paid tx's in the specified database."""
    infura_key = ''
    if chain_provider == 'infura':
        infura_key = click.prompt(
            'Please enter your infura key', type=str)

    w3 = get_chain(chain_provider, chain_name, infura_key=infura_key)

    q = """
    SELECT id, txid
     FROM txs
     WHERE success = 0 AND txid IS NOT NULL;
    """
    for id_, txid in query_all(db_file, q):
        if is_tx_successful(w3, txid):
            mark_tx_as_successful(db_file, id_)
            print(f'{txid} is OK.')
        else:
            reason = 'Out of Gas' if is_tx_out_of_gas(w3, txid) else 'Fail'
            if click.confirm(f'{txid} has failed ({reason}). Retry?'):
                mark_tx_for_retry(db_file, id_)


if __name__ == '__main__':
    cli()
