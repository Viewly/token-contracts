## csv2json.py
This script will convert .csv files from Google Sheet
to `distribute.py` compliant json.

Example usage:
```
python csv2json.py \
    example_data/payout-sheet.csv \
    example_data/address-book.csv \
        > payouts.json
```

*The .csv files can be found
[here](https://docs.google.com/spreadsheets/d/1cBV168xNWoQbcqnIjiRi3vN0Lf6d1-i9GDIQ-1HrkoA/edit?pli=1#gid=1500784426),
by exporting tabs "Payout Sheet" and "Address Book"*

## distribute.py

Import a payouts.json file into its own database:
```
python distribute.py import-txs payouts.json payouts.db
```

Issue Payouts:
```
python scripts/distribute.py payout \
    --provider geth --chain mainnet \
    --owner 0xaAF3FFEE9d4C976aA8d0CB1bb84c3C90ee6E9118 \
    --db-file payouts.db \
    --contract-address 0x7cedd8ae603c3513fe7e86be4adb0314b0e8ec50 \
    --abi-path build/MintTokens.abi.json
```

Verify Payouts:
```
python scripts/distribute.py verify \
    --provider geth --chain mainnet \
    --db-file payouts.db
```

---

### Sqlite
Check the transactions in sqlite:
```
~/scripts % sqlite3 payouts.db "select * from txs;"
1|0x9cd47749bcd550ce4d2590a82fad16eec9d007b7|1000.0|0||0
2|0x9cd47749bcd550ce4d2590a82fad16eec9d007b7|100.0|1||0
```

### Exporting the table as .csv
```
sqlite3 -header -csv payouts.db "select * from txs;" > out.csv
```
