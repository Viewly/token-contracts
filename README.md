![](https://i.imgur.com/ekvJd60.png)

*Viewly is building a decentralized YouTube, with crypto powered monetization models for
content creators.*  
Learn more at https://view.ly

## Introduction
We have built a flexible Ethereum crowdfunding contract, that allows us to to sell
ERC-20 tokens to raise funds for development and growth of our **decentralied video platform**.

This document has been created to explain the Viewly smart contract in **Plain English**, so that non-developers can understand the mechanics of the Viewly Crowdsale. We will also use this opportunity to clarify our intentions, and explain why we made certain decisions.

## TL;DR
There are three properties of our crowdfund model:  
1.) Multiple Sales (Rounds), to mimick Seed, Series A, B, C... from startup world.  
2.) Contract enforced release for purposes of vesting, the bounty program, influencer outreach, and rewards for community contributors.  
3.) Migration mechanism, to burn and claim the platform native tokens.


## Hard Cap
The `ViewlySale` contract has an immutable hard cap of 100M VIEW tokens.
The contract can be used to create multiple sales, for smaller portions of the hard cap.

## Multiple Funding Events
`ViewlySale` contract can run multiple crowdsale events. This will allow us to follow a more traditional funding model, with a pre-sale (series A), followed by one or two funding events as our project progresses.

A simple state machine dictates the correct behavior of the `ViewlySale` contract during different phases of the sale. 
```
enum State {
    Pending,
    Running,
    Done
}
State public state = State.Pending;
```
As mentioned earlier, we can have multiple sale events, as long as the hard cap of 100M tokens is not reached. While the sale is ongoing, it is not possible to start another sale,  claim VIEW tokens or issue reserved supply.


## ETH and Token capped Auction Sale
We believe its in the projects best long-term interest to limit the amount of
coins to be sold, as well as the dollar amount of receivables (ETH).
In other words, we would like to sell enough tokens to execute on R&D,
influencer outreach, marketing and the main crowdfund event.
By hard-capping the dollar value of the pre-sale, we ensure the leeway for a much higher implied market-cap for the main crowdsale.

Capped auction is a buyer-friendly alternative to the fixed price sale. Combined with the fixed USD and token cap for each auction, we can curb the irrational exuberance, and aim for a more organic growth.

This execution type will also improve the health of our project by further aligning our incentives for the long-term success.

### Example Scenarios
Please note, that these scenarios are made up, and only serve as an example of how the `ViewlySale` contract allocates the tokens.

In this hypothetical example, 10M VIEW tokens are for sale (10% of the hard-cap), and we are buying in with $1 million worth of ETH. Lets see what would happen in 3 different scenarios (see *Round Raised* and *Price per VIEW* columns).

| Round Tokens Cap | Round ETH Cap ($) | Round Raised | $1M Receives  | Price per VIEW |
| ---------------- | ----------------- | ------------ | ------------- | -------------- |
| 10M VIEW (10%)   | 10M USD           | 2M USD       | 5M VIEW (10%) | $0.2           |
| 10M VIEW (10%)   | 10M USD           | 5M USD       | 2M VIEW (2%)  | $0.5           |
| 10M VIEW (10%)   | 10M USD           | 10M USD      | 1M VIEW (1%)  | $1.0           |

Hypothetically speaking, the Viewly project gains serious traction, and readies itself for the main crowdsale. Again, we are hypothetically buying in with $1 million worth of ETH.

| Round Tokens Cap | Round ETH Cap ($) | Round Raised | $1M Receives | Price per VIEW |
| ---------------- | ----------------- | ------------ | ------------ | -------------- |
| 30M VIEW (30%)   | 150M USD          | 50M USD      | 0.6M VIEW    | $1.67          |
| 30M VIEW (30%)   | 150M USD          | 100M USD     | 0.3M VIEW    | $3.3           |
| 30M VIEW (30%)   | 150M USD          | 150M USD     | 0.2M VIEW    | $5.0           |


## Liquidity
The ERC-20 VIEW Tokens become liquid immediately after the sale is closed (the price is not known until the end).
Users need to claim their ERC-20 View tokens manually, because Ethereum is not capable of storing or iterating a list of purchases.
This is done simply by calling `claim(roundNumber)`. Claims can be made for current and past rounds, at any time.


## Reserved Supply and Vesting
Reserved supply is used to incentivize the development team, fund the bounty program, and the influencer outreach.

The creation of reserved supply has been decoupled from the sale event. `ViewlySale` contract is capable of issuing reserved supply on demand, however a rate limit
of up to 2% of total token supply per month is imposed by the contract.
This **vesting schedule** creates artificial scarcity in the supply of tokens available to Viewly, which forces us to be more prudent in regards to our spending, and incentivizes long-term thinking.

## Predictable Float
The vesting schedule based release of the reserved allocation also acts as a
remedy against uncertanty of implied valuations due to the unpredictable float
![](https://i.imgur.com/FNHIi3L.png)  
*[Source](https://blog.coinfund.io/toward-more-equitable-token-sale-structures-a71db12c8aff)*

In Viewly's model, the unsold tokens are simply not available, and cannot be used
for insider trading or market manipulation.
The tokens can be minted at a fixed vesting schedule up to 2% per month, and
the majority of these tokens should be transparently allocated via the
Bounty Program and/or the Worker Proposal system (TBA).

## Code is law
We believe that the crowdsale contract should be immutable.
In our view, changing the terms of the crowdsale or the behaviour of the crowdsale contract after the crowdsale has started is shady, if not outright fraudulent.

### No backdoors
This contract is *non upgradable*. Owners of the contract have **no ability** to transfer or burn people's VIEW tokens.
We believe that such features leave the door open for abuse, and decrease the trustworthiness of the token.

### No Gas Limit
This sale contract will have no `tx.gasprice` limit.

Setting a gas limit, in combination with high transaction volume might clog the Ethereum network (see Bancor and Status).
![](https://i.imgur.com/dlNarkq.png)

### Targeting Sophisticated Buyers
Having no gas limit enables sophisticated buyers to perform crowdsale *sniping*. 
By jacking up the gas price, they are able to skip the queue, and get their tokens before the *retail* buyers. We believe that this is acceptable, since we don't want to have too many *retail* buyers. The rationale is that the sophisticated buyers that are capable of performing the *sniping* are more likely to be the whales,
and crypto veterans, and as such, they are most likely to be experienced speculators.

### Crowdsale is not an efficient token distribution
We don't believe that the crowdsale is an efficient token distribution.

We think that the tokens will be most effective in the hands of content creators and their audiences.

For this reason, we will set up an official faucet, and fairly distribute a portion of the tokens (see Reserved Supply), to the content creators and their fans, once our chain launches.

## Convertibility
Viewly ERC-20 tokens issued on Ethereum will be convertible into native Viewly tokens when our network launches (in a 1:1 ratio). This is achieved trough the `registerAndBurn(bytes32 viewlyAddr, uint amount)` function in `ViewlySale` contract. Calling this contract will register your native Viewly address, and burn the tokens in the process.

### One to many mapping
In the future version of this contract, it will be possible to register any number of Viewly addresses, as well as burn arbitrary amounts. This would allow users to split their ERC-20 tokens into multiple Viewly accounts, as well as provide exchanges with an easy way to convert the tokens for their clients.


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
py.test tests/
```

## Running on a testnet
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


Then you can deploy the contract to given chain with:
```
python deploy.py {ropsten|rinkeby|mainnet}
```

## Contract Viewer
Afterwards deploying to testnet, you can run the web app to interact with the contract:
```
cd app
export FLASK_APP=src/server.py
flask run
```
