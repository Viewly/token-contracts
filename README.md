## Introduction
This document has been created to explain the smart contract in **Plain English**, so that people whom aren't developers can undestand 
the mechanics of the Viewly Crowdsale. We will also use this opportunity to explain our intentions, and why did we make certain decisions.


## No Gas Limit
This sale contract will have no gas limit.

**Don't clog the network**  
Setting a gas limit might clog the Ethereum network (see Bancor sale).

**Sophisticated Buyers**
Having no gas limit enables sophisticated buyers to perform crowdsale *sniping*. By jacking up the gas price, they are
able to skip the queue, and get their tokens before the *retail* buyers.
We believe that this is the desired behaviour, since we don't want to have too many *retail* buyers.
The rationale is that the sophisticated buyers that are capable of performing the *sniping* are more likely to be the whales,
and crypto veterans, and as such, they are most likely to be experienced speculators.

**Crowdsale is not an efficient token distribution**
We don't believe we can make a crowdsale that is the efficient token distribution.
The reason for this, is that the tokens will be most effective in the hands of content creators and their audiences.
There is a very small overlap between our target users, and the speculators buying into Ethereum crowdsales.

For this reason, we will set up an official faucet, and fairly distribute a portion of the tokens that are held back,
to the content creators and their fans, once our chain launches.

## Code is law
We believe that the crowdsale contract should be immutable. 
In our view, changing the terms of the crowdsale or the behaviour of the crowdsale contract after the crowdsale has started is shady, if not outright fraudulent.

Furthermore, this contract is *non upgradable*, and it provides no capability to *mint* new tokens, or *burn* people's tokens.
We believe that such features leave the door open for abuse, and decrease the trustworthiness of the token.