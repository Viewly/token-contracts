import click
import json
import csv
from typing import List


def csv_to_dict(csv_file: str) -> List[dict]:
    """
    Convert a multi-column .csv file into
    a list of dictionaries.
    """
    with open(csv_file, 'rt') as f:
        reader = csv.DictReader(f)
        return [dict(x) for x in reader]

def get_address(name, address_book):
    return [x for x in address_book if x['Name'] == name][0]

def rename_field(field_name):
    rename = {
        "Tokens": "amount",
        "Address": "recipient",
        "Bucket": "bucket",
    }
    return rename.get(field_name, '')

def merge_and_clean(payout_sheet, address_book):
    merged = [
        {**payout, **get_address(payout['Name'], address_book)}
        for payout in payout_sheet
    ]
    cleaned_up = [
        {rename_field(k): v for k, v in item.items() if rename_field(k)}
        for item in merged
    ]
    return cleaned_up

def pretty_json(data) -> str:
    return json.dumps(data, indent=2)


@click.command()
@click.argument('payout-sheet-csv', type=click.Path(exists=True))
@click.argument('address-book-csv', type=click.Path(exists=True))
def convert(payout_sheet_csv, address_book_csv):
    """
    Take input .csv files, merge them, and spit out
    distribute.py compliant .json (to stdout).
    """
    data = merge_and_clean(
        address_book = csv_to_dict(address_book_csv),
        payout_sheet = csv_to_dict(payout_sheet_csv),
    )
    click.echo(pretty_json(data))

if __name__ == '__main__':
    convert()
