import click
import os
import web3

from web3.utils.validation import validate_address
from toolz import pipe, keymap
from eth_utils import to_wei
from pathlib import Path

from utils import (
    load_json,
    get_chain,
    default_wallet_account,
    unlock_wallet,
    load_csv_to_dict,
)
from db import (
    init_db,
    import_txs,
    query_all,
    update_txid,
    mark_tx_as_successful,
    mark_tx_for_retry,
)

roles = 'Team Supporters Creators Bounties SeedSale MainSale'.split(' ')
buckets = dict(zip(roles, range(len(roles))))

def rename_field(field_name):
    # these are the standard fields
    if field_name.lower() in ['name', 'amount', 'recipient', 'bucket']:
        return field_name.lower()

    # these are here for compatibility with Speadsheet headers
    rename = {
        'Tokens': 'amount',
        'Address': 'recipient',
        'Bucket': 'bucket',
        'Category': 'bucket',
    }
    return rename.get(field_name, '')

def validated_payouts(payouts_in):
    """
    This method validates json transactions.
    It ensures `recipient` addresses are valid ETH addresses,
    and expands `bucket` aliases into proper bucket_id's.
    """
    # swap bucket name with matching ID
    payouts = [
        {
            **x,
            'bucket': buckets[x['bucket']],
            'amount': float(x['amount'].replace(',', '')),
        }
        for x in (keymap(rename_field, y) for y in payouts_in)
    ]

    # validate addresses
    for payout in payouts:
        validate_address(payout['recipient'])

    return payouts


def txs_from_file(filename: str) -> dict:
    """
    Load a payout sheet that adheres to Google Sheet
    csv or the standardized json input.
    """
    extension = filename.split('.')[-1]
    if extension == 'json':
        loader_fn = load_json
    elif extension == 'csv':
        loader_fn = load_csv_to_dict
    else:
        raise ValueError(f'Unsupported file type "{extension}"')

    return pipe(
        filename,
        loader_fn,
        validated_payouts,
    )

def get_token_mintage_instance(
    w3: web3.Web3,
    abi_path: str,
    contract_address: str) -> web3.eth.Contract:
    """ Reconstruct a contract instance from its address and ABI."""
    abi = load_json(abi_path)
    return w3.eth.contract(abi, contract_address)


def mint_tokens(
    instance: web3.eth.Contract,
    owner: str,
    recipient: str,
    amount: float,
    bucket: int, **kwargs) -> str:
    """ Call `mint` function on target contract.

    Args:
        instance: A ViewTokenMintage live and initialized contract instance.
        owner: An authorized Ethereum account to call the minting contract from.
        recipient: Address of VIEW Token Recipient.
        amount: Amount of VIEW Tokens to mint.
        bucket: A bucket number of the funding source (Team, Supporters...)

    Returns:
        txid: Transaction ID of the function call
    """
    assert bucket in buckets.values(), "Invalid bucket id"
    assert type(amount) == float, "Invalid amount type"
    validate_address(recipient)

    tx_props = {
        'value': 0,
        'from': owner,
    }
    # if gas limit is not provided,
    # w3.eth.estimateGas() is usded
    if 'gas' in kwargs:
        tx_props['gas'] = kwargs['gas']

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
@click.argument('payout-sheet-file', type=click.Path(exists=True))
@click.argument('db-file', required=False, type=click.Path(exists=False))
def cli_import_txs(payout_sheet_file, db_file):
    """Import transactions from json file to a new database for processing."""
    txs = txs_from_file(payout_sheet_file)

    db_file = db_file or f'{Path(payout_sheet_file).stem}.db'
    if os.path.exists(db_file):
        click.confirm(f'Database {db_file} already exists. Overwrite?',
                      abort=True)

    init_db(db_file)
    import_txs(db_file, txs)
    print(f'Imported {len(txs)} transactions into {db_file}')

@cli.command(name='payout')
@click.option('--provider', 'chain_provider', default='parity', type=str,
              help='Chain Provider (parity, geth, tester...)')
@click.option('--chain', 'chain_name', default='mainnet', type=str,
              help='Name of ETH Chain (mainnet, kovan, rinkeby...)')
@click.option('--owner', default=None, type=str,
              help='Account to call the contract from')
@click.option('--contract-address', prompt=True, type=str,
              help='Address of ViewTokenMintage contract')
@click.option('--abi-path', default='build/view_token_mintage.abi.json',
              type=click.Path(exists=True),
              help='ABI of the token minting contract')
@click.argument('db-file', type=click.Path(exists=True))
def cli_payout(
    chain_provider,
    chain_name,
    owner,
    contract_address,
    abi_path,
    db_file):
    """Payout pending tx's in the specified database."""

    w3 = get_chain(chain_provider, chain_name)
    if not owner:
        owner = default_wallet_account(w3)
    if chain_name not in ['tester', 'testrpc']:
        unlock_wallet(w3, owner)

    instance = get_token_mintage_instance(w3, abi_path, contract_address)
    assert instance.address.lower() == contract_address.lower()

    q = """
    SELECT id, recipient, amount, bucket
     FROM txs
     WHERE txid IS NULL AND success = 0;
    """
    for payout in query_all(db_file, q):
        id_, recipient, amount, bucket = payout
        txid = mint_tokens(
            instance, owner, recipient, amount, bucket,
        )
        update_txid(db_file, id_, txid)
        print(f'Minted {amount} tokens to {recipient}')


@cli.command(name='verify')
@click.option('--provider', 'chain_provider', default='parity', type=str,
              help='Chain Provider (parity, geth, tester...)')
@click.option('--chain', 'chain_name', default='mainnet', type=str,
              help='Name of ETH Chain (mainnet, kovan, rinkeby...)')
@click.argument('db-file', type=click.Path(exists=True))
def cli_verify(chain_provider, chain_name, db_file):
    """Verify paid tx's in the specified database."""
    w3 = get_chain(chain_provider, chain_name)

    q = """
    SELECT id, txid
     FROM txs
     WHERE success = 0 AND txid IS NOT NULL;
    """
    for id_, txid in query_all(db_file, q):
        try:
            success = is_tx_successful(w3, txid)
        except:
            print(f'Unable to verify {txid}. Try again later.')
            continue
        if success:
            mark_tx_as_successful(db_file, id_)
            print(f'{txid} is OK.')
        else:
            reason = 'Out of Gas' if is_tx_out_of_gas(w3, txid) else 'Fail'
            if click.confirm(f'{txid} has failed ({reason}). Retry?'):
                mark_tx_for_retry(db_file, id_)

@cli.command(name='export-txs')
@click.option('--chain', 'chain_name', default='mainnet', type=str,
              help='Name of ETH Chain (mainnet, kovan, rinkeby...)')
@click.argument('db-file', type=click.Path(exists=True))
def cli_export_txs(chain_name, db_file):
    """Export the database into a Google Sheet friendly csv."""
    q = """
    SELECT name, recipient, amount, bucket, txid, success FROM txs;
    """
    click.echo('Name,Address,Amount,Category,Tx,Success')
    for name, recipient, amount, bucket, txid, success in query_all(db_file, q):
        subdomain = '' if chain_name == 'mainnet' else f'{chain_name}.'
        buckets_reverse = {v:k for k, v in buckets.items()}
        click.echo(
            f'{name},{recipient},{amount},{buckets_reverse[bucket]},'
            f'https://{subdomain}etherscan.io/tx/{txid},{success}')

if __name__ == '__main__':
    cli()
