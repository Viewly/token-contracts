## distribute.py
distribute.py is a tool for Minting Tokens.

First, we create a database from .json or .csv payout sheet.
Once the database is created, the script can:
 - payout (mint tokens)
 - verify transactions on the blockchain
 - export the results to .csv

Import a `payouts.json` file into its own database:
```
python distribute.py import-txs payouts.json payouts.db
```

Alternatively, this script also supports Google Payouts Sheet exported as .csv
```
python distribute.py import-txs payout-sheet.csv payouts.db
```

Make the payouts (from the database):
```
python scripts/distribute.py payout \
    --contract-address 0x7cedd8ae603c3513fe7e86be4adb0314b0e8ec50 \
    payouts.db
```

Verify Payouts on the blockchain:
```
python scripts/distribute.py verify payouts.db
```

---

### Export the database as a Google Sheets friendly csv
```
python scripts/distribute.py export-txs payouts.db
```
