## distribute.py

Import a payouts.json file into its own database:
```
python distribute.py import-txs ../payments-december.json december.db
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

## Sqlite
Check the transactions in sqlite:
```
~/scripts % sqlite3 december.db "select * from txs;"
1|0x9cd47749bcd550ce4d2590a82fad16eec9d007b7|1000.0|0||0
2|0x9cd47749bcd550ce4d2590a82fad16eec9d007b7|100.0|1||0
```
