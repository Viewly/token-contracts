DROP TABLE IF EXISTS txs;

CREATE TABLE txs (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    recipient CHAR(42) NOT NULL,
    amount FLOAT NOT NULL,
    bucket INTEGER NOT NULL,
    txid CHAR(66) DEFAULT NULL,
    success Boolean DEFAULT 0
);

CREATE UNIQUE INDEX unique_payment ON txs (recipient, amount, bucket);
