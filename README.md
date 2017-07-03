## Introduction
This document has been created to explain the smart contract in **Plain English**, so that people whom aren't developers can understand
the mechanics of the Viewly Crowdsale. We will also use this opportunity to clarify our intentions, and explain why we made certain decisions.

## Code is law
We believe that the crowdsale contract should be immutable.
In our view, changing the terms of the crowdsale or the behaviour of the crowdsale contract after the crowdsale has started is shady, if not outright fraudulent.

### No backdoors
Furthermore, this contract is *non upgradable*, and it provides no capability to *mint* new tokens, or *burn* people's tokens.
We believe that such features leave the door open for abuse, and decrease the trustworthiness of the token.

### No Gas Limit
This sale contract will have no `tx.gasprice` limit.

### Don't clog the network
Setting a gas limit, in combination with high transaction volume might clog the Ethereum network (see Bancor and Status).
![](http://i.imgur.com/dlNarkq.png)

### Targeting Sophisticated Buyers
Having no gas limit enables sophisticated buyers to perform crowdsale *sniping*. By jacking up the gas price, they are
able to skip the queue, and get their tokens before the *retail* buyers.
We believe that this is the desired behaviour, since we don't want to have too many *retail* buyers.
The rationale is that the sophisticated buyers that are capable of performing the *sniping* are more likely to be the whales,
and crypto veterans, and as such, they are most likely to be experienced speculators.

### Crowdsale is not an efficient token distribution
We don't believe we can make a crowdsale that is the efficient token distribution.
The reason for this, is that the tokens will be most effective in the hands of content creators and their audiences.
There is a very small overlap between our target users, and the speculators buying into Ethereum crowdsales.

For this reason, we will set up an official faucet, and fairly distribute a portion of the tokens that are held back,
to the content creators and their fans, once our chain launches.

## Convertibility
Viewly ERC-20 tokens issued on Ethereum will be convertible into native Viewly tokens when our network launches (in a 1:1 ratio). This is achieved trough the `registerAndBurn(bytes32 viewlyAddr, uint amount)` function in `ViewlySale` contract. Calling this contract will register your native Viewly address, and burn the tokens in the process.

### One to many mapping
In the future version of this contract, it will be possible to register any number of Viewly addresses, as well as burn arbitrary amounts. This would allow users to split their ERC-20 tokens into multiple Viewly accounts, as well as provide exchanges with an easy way to convert the tokens for their clients.


# Proposed Contract :: ViewlySale

## Single Funding Event
`ViewlySale` contract is designed for a single and large crowdfunding event, with guaranteed
fixed reserved supply.

## Fair and Predictable Reserves Allocation
As an example, lets look at BAT's sale contract. In BAT's case, the reserved tokens are allocated before the sale.
This means, that we cannot know in advance what % of the tokens has been held back. It could be anywhere between 30% and 75%.
```solidity
    uint256 public constant batFund = 500 * (10**6) * 10**decimals;   // 500m BAT reserved for Brave Intl use
    uint256 public constant tokenExchangeRate = 6400; // 6400 BAT tokens per 1 ETH
    uint256 public constant tokenCreationCap =  1500 * (10**6) * 10**decimals;
    uint256 public constant tokenCreationMin =  675 * (10**6) * 10**decimals;


    // constructor
    function BAToken(
        address _ethFundDeposit,
        address _batFundDeposit,
        uint256 _fundingStartBlock,
        uint256 _fundingEndBlock)
    {
      isFinalized = false;                   //controls pre through crowdsale state
      ethFundDeposit = _ethFundDeposit;
      batFundDeposit = _batFundDeposit;
      fundingStartBlock = _fundingStartBlock;
      fundingEndBlock = _fundingEndBlock;
      totalSupply = batFund;
      balances[batFundDeposit] = batFund;    // Deposit Brave Intl share
      CreateBAT(batFundDeposit, batFund);  // logs Brave Intl fund
    }

```


In the Viewly contract however, we allocate the reserves **after** the crowdsale window ends. This way we can guarantee that the reserved allocation will be exactly the pre-set fixed %, regardless of how many tokens are sold.

We perform the allocation in `finalizeSale()`, and we guarantee that exactly 20% of the token supply will be reserved:
```solidity
uint128 public constant tokenCreationCap = 100000000;   // 100_000_000
uint128 public constant reservedAllocation = 0.2 ether; // 20%

function calcReservedSupply() constant returns(uint256) {
    uint256 totalSupply = VIEW.totalSupply();
    uint256 supplyPct = sub(1, reservedAllocation);
    uint256 reservedSupply = mul(div(totalSupply, supplyPct), reservedAllocation);
    return reservedSupply;
}
```


# Alternate Contract :: ViewlySaleRecurrent

## Multiple Funding Events
Should we aim for a more traditional funding model, with a pre-sale (series A), followed by one or two funding events as our project progresses, the `ViewlySaleRecurrent` contract should be used.

A simple state machine dictates the correct behavior of the `ViewlySale` contract during different phases of the sale. In `ViewlySaleRecurrent`, there can be multiple sale events, as long as the hard cap of 100M tokens is not reached. While the sale is ongoing, it is also not possible to issue reserved supply.
```
enum State {
    Pending,
    Running,
    Done
}
State public state = State.Pending;
```

Aside from the ability to have multiple sale events from the single contract, this proposal also changes the behavior of the reserved supply.

## Reserved Supply and Vesting
Reserved supply is to be used to incentivize the development team, fund the bounty program as well as the influencer outreach.

The creation of reserved supply has been decoupled from the sale event. `ViewlySaleRecurrent` contract is now capable of issuing reserved supply on demand, however a rate limit
of 2% of total token supply per month is imposed by the contract.
This *vesting schedule* creates artificial scarcity in the supply of tokens available to Viewly, which forces us to be more prudent in regards to our spending, and incentivizes long-term thinking.

# Capped Auction Contract :: ViewlyAuctionRecurrent
Capped auction is a buyer-friendly alternative to the fixed price sale. Combined with the fixed USD and token cap for each auction, we can curb the irrational exuberance, and aim for a more organic growth.

This execution type will also improve the health of our project by further aligning our incentives for the long-term success.
