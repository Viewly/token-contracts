import click
import os

from web3.utils.validation import validate_address
from toolz import pipe

from utils import load_json
from db import init_db, import_txs

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


def mint_contract():
    chain_name = 'testrpc'
    mint_tokens_addr = ''

    with Project().get_chain(chain_name) as chain:

        owner = chain.web3.eth.coinbase
        mint_tokens_contract = load_contract(chain, 'MintTokens', bounty_address)

def mint_tokens(
    recipient: str,
    amount: float,
    bucket: int) -> str:
    pass

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
def cli_payout(db_file):
    """Payout pending tx's in the specified database."""
    q = """
    SELECT * FROM txs WHERE txid IS NULL;
    """

@cli.command(name='verify')
@click.argument('db-file', type=click.Path(exists=True))
def cli_verify(db_file):
    """Verify paid tx's in the specified database."""
    q = """
    SELECT * FROM txs WHERE success = 0 AND txid IS NOT NULL;
    """

if __name__ == '__main__':
    cli()
