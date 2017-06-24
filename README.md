## Introduction
This document has been created to explain the smart contract in **Plain English**, so that people whom aren't developers can undestand 
the mechanics of the Viewly Crowdsale. We will also use this opportunity to clarify our intentions, and explain why we made certain decisions.


## No Gas Limit
This sale contract will have no gas limit.

### Don't clog the network
Setting a gas limit might clog the Ethereum network (see Bancor sale).

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

## Code is law
We believe that the crowdsale contract should be immutable. 
In our view, changing the terms of the crowdsale or the behaviour of the crowdsale contract after the crowdsale has started is shady, if not outright fraudulent.

### No backdoors
Furthermore, this contract is *non upgradable*, and it provides no capability to *mint* new tokens, or *burn* people's tokens.
We believe that such features leave the door open for abuse, and decrease the trustworthiness of the token.


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



In the Viewly contract however, we allocate the reserved tokens **after** the crowdsale is complete.
This way we guarantee that the reserved allocation will be exactly the pre-set fixed %, regardless of how many tokens are sold.

With the code below, exactly 20% of the token supply will be reserved:
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