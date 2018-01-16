![](https://i.imgur.com/ekvJd60.png)

*Viewly is building a decentralized video platform.* Learn more at https://view.ly

[![CircleCI](https://circleci.com/gh/Viewly/token-contracts.svg?style=svg&circle-token=1e0971075338fce5801b9f32a1e709c2692e49e0)](https://circleci.com/gh/Viewly/token-contracts)
# Viewly Token Contracts

## Dependencies
Viewly smart contracts are leveraging the
[Dappsys](https://dappsys.readthedocs.io/en/latest/) framework, because Dappsys
provides clean and well written implementations of things like safe math, ERC-20
token and multisig.

We are also using [Populus](http://populus.readthedocs.io/en/latest/) as a
development framework. The Viewly contract testing is fully automated, and the
tests are written in Python.

For managing dependencies we use [Pipenv](https://pypi.python.org/pypi/pipenv).
Make sure you have it installed.

To install all project dependencies, run:
```
pipenv install
```

## Running locally (inside pipenv shell):
To compile the contracts, run:
```
populus compile
```

To test the contracts, run:
```
pytest
```

To deploy the contract(s) run their deployment script:
```
python deploy/seed_sale.py <args...>
```

## Running on testrpc
First, we need to spin up testrpc [server](https://github.com/pipermerriam/eth-testrpc):
```
testrpc-py
```

Then, we can deploy contracts by providing `testrpc` as chain, for example:
```
python deploy/seed_sale.py --chain testrpc <args...>
```


## Running on a testnet (geth)
If you've just installed `geth`, you need to create a new account
and send some `ropsten` tokens to it:
```
geth --testnet account new
```

To deploy the contracts to the testnet (Ropsten),
make sure you have local `geth` running first:
```
geth --testnet --fast --etherbase "0x25b99234a1d2e37fe340e8f9046d0cf0d9558c58"
```
*The etherbase account is the `owner` in the deployer scripts.*

Then you can deploy the contract to testnet with given multisig address as
beneficiary with:
```
python deploy/seed_sale.py --chain ropsten <args...>
```

## Deploying to production
Make sure you are running mainnet node (parity or geth) with RPC/HTTP interace
open.

Deploy sale contract with:
```
python deploy/seed_sale.py --chain mainnet <args...>
```

Deploy token mintage contract with:
```
python deploy/token_mintage.py --chain mainnet <args...>
```

## Deployed contracts
- [ViewToken](https://etherscan.io/address/0xf03f8d65bafa598611c3495124093c56e8f638f0)
- [ViewTokenMintage](https://etherscan.io/address/0xf665069A0eE102CeADbd80690814473DbDd56AC8)
- [ViewlySeedSale](https://etherscan.io/address/0xdbdb79ad0a2243c947cc413798e8b90caba0b9df)
