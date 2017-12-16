![](https://i.imgur.com/ekvJd60.png)

*Viewly is building a decentralized YouTube, with crypto powered monetization models for
content creators.*  
Learn more at https://view.ly

# Instructions

## Dependencies
Viewly smart contracts are leveraging the [Dappsys](https://dappsys.readthedocs.io/en/latest/) framework, because Dappsys provides clean and well written implementations of things like safe math, ERC-20 token and multisig.

We are also using [Populus](http://populus.readthedocs.io/en/latest/) as a development framework. The Viewly contract testing is fully automated, and the tests are written in Python.

## Running Locally
To compile the contracts, run:
```
populus compile
```

To test the contracts, run:
```
pytest tests/
```

To deploy the contract(s) run their deployment script:
```
python deploy/seed_sale.py <chain> <beneficiary_address>
```

## Running on testrpc
First, we need to spin up testrpc [server](https://github.com/pipermerriam/eth-testrpc):
```
testrpc-py
```

Then, we can deploy contracts by providing `testrpc` as chain, for example:
```
python deploy/seed_sale.py testrpc 0xabc...d
```


## Running on a testnet (geth)
If you've just installed `geth`, you need to create a new account
and send some `ropsten` tokens to it:
```
geth --testnet account new
```
*The default password used by the deployment script is `test`*.

To deploy the contracts to the testnet (Ropsten),
make sure you have local `geth` running first:
```
geth --testnet --etherbase "0x25b99234a1d2e37fe340e8f9046d0cf0d9558c58"
```
*The etherbase account is the main account that will be creating the contract.*


Then you can deploy the contract to testnet with given multisig address as
beneficiary with:
```
python deploy/seed_sale.py ropsten "0xcbb09f94680f10887f1c358df9aea5c425a1f0b8"
```

Similarily, you can also deploy to other configured chains such as rinkeyb:
```
python deploy/seed_sale.py rinkeby "0xcbb09f94680f10887f1c358df9aea5c425a1f0b8"
```

## Running on a testnet (parity)
```
parity --light --chain=kovan --ui-port 8080 ui
```

## Contract Viewer
After deploying to testnet, you can run the web app to interact with the contract:
```
cd app
export FLASK_APP=src/server.py
flask run
```
