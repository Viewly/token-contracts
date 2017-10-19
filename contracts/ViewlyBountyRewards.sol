// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.16;

import "./dappsys/math.sol";
import "./dappsys/token.sol";
import "./dappsys/auth.sol";

/* ViewlyBountyRewards is a simple contract that allows distributing VIEW tokens
   earned through Viewly Bounty program.
 */
contract ViewlyBountyRewards is DSAuth, DSMath {
    // total tokens rewarded is capped at 3% of token supply
    uint constant public MAX_TOKEN_REWARDS = 3000000 ether;

    // VIEW token contract
    DSToken public viewToken;

    uint public totalTokenRewards;
    mapping (address => uint) public tokenRewards;


    event LogTokenReward(
        address recipient,
        uint tokens
    );


    function ViewlyBountyRewards(DSToken viewToken_) {
        viewToken = viewToken_;
    }

    function sendTokenReward(address recipient, uint tokens) auth {
        require(tokens > 0);
        require(add(tokens, totalTokenRewards) <= MAX_TOKEN_REWARDS);

        tokenRewards[recipient] += tokens;
        totalTokenRewards = add(tokens, totalTokenRewards);

        viewToken.mint(recipient, tokens);
        LogTokenReward(recipient, tokens);
    }
}
