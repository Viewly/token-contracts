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
python distribute.py import-txs payouts.json december.db
```

Issue Payouts:
```
python distribute.py payout december.db
```

Verify Payouts:
```
python distribute.py verify december.db
```

---

### Sqlite
Check the transactions in sqlite:
```
~/scripts % sqlite3 december.db "select * from txs;"
1|0x9cd47749bcd550ce4d2590a82fad16eec9d007b7|1000.0|0||0
2|0x9cd47749bcd550ce4d2590a82fad16eec9d007b7|100.0|1||0
```

### Exporting the table as .csv
```
sqlite3 -header -csv december.db "select * from txs;" > out.csv
```
