// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.16;

import "./lib/math.sol";
import "./lib/token.sol";
import "./lib/auth.sol";

/* Viewly seed token sale contract, where buyers send ethers to receive ERC-20
 * VIEW tokens in return. It features:
 * - instant token payback when eth is sent
 * - hard-coded ETH contributions and VIEW token hard-caps
 * - sale start time and duration is set after deploy
 * - sale can be ended anytime after start
 * - deposits can be collected any time after sale starts
 *
 * Amount of VIEW tokens send back to buyers decreases linearly: early buyers
 * get bonus tokens over last buyer. Bonus is maximal at the beginning (15%) and
 * gradually lowers as deposits are sent in. It is finally reduced to zero as
 * eth cap is reached. Token bonus also applies inside a single purchase:
 * even the first buyer gets lower average bonus if sends in more ethers. If
 * first buyer sends in 4000 eth (eth cap), his average bonus will be half of
 * max bonus because his purchase spans from max bonus to 0 bonus (end of sale).
 *
 * The sale always reaches eth contributions and token caps simultaneously.
 * Average amount of tokens per eth sent will always be the same
 * (and equal to TOKEN_CAP/ETH_CAP).
 */
contract ViewlySeedSale is DSAuth, DSMath {

    uint constant public ETH_CAP =           4000 ether;   // ether hard-cap
    uint constant public TOKEN_CAP = 10 * 1000000 ether;   // token hard-cap
    uint constant public BONUS =             0.15 ether;   // bonus of tokens early buyers
                                                           // get over last buyers

    DSToken public viewToken;         // VIEW token contract
    address public beneficiary;       // destination to collect eth deposits
    uint public startBlock;           // start block of sale
    uint public endBlock;             // end block of sale

    uint public totalEthDeposited;    // sums of ether raised
    uint public totalTokensBought;    // total tokens issued on sale
    uint public totalEthCollected;    // total eth collected from sale

    // buyers ether deposits
    mapping (address => uint) public ethDeposits;

    enum State {
        Pending,
        Running,
        Ended
    }
    State public state = State.Pending;

    event LogBuy(
        address buyer,
        uint ethDeposit,
        uint tokensBought
    );

    event LogStartSale(
        uint startBlock,
        uint endBlock
    );

    event LogEndSale(
        uint totalEthDeposited,
        uint totalTokensBought
    );

    modifier salePending() { require(state == State.Pending); _; }
    modifier saleRunning() { require(state == State.Running); _; }
    modifier saleEnded() { require(state == State.Ended); _; }

    // check current block is inside closed interval [startBlock, endBlock]
    modifier inRunningBlock() {
        require(block.number >= startBlock);
        require(block.number < endBlock);
        _;
    }
    // check sender has sent some ethers
    modifier ethSent() { require(msg.value > 0); _; }


    // PUBLIC //

    function ViewlySeedSale(DSToken viewToken_, address beneficiary_) {
        viewToken = viewToken_;
        beneficiary = beneficiary_;
    }

    function() payable {
        buyTokens();
    }

    function buyTokens() saleRunning inRunningBlock ethSent payable {
        uint128 tokensBought = calcTokensForPurchase(msg.value, totalEthDeposited);
        ethDeposits[msg.sender] = add(msg.value, ethDeposits[msg.sender]);
        totalEthDeposited = add(msg.value, totalEthDeposited);
        totalTokensBought = add(tokensBought, totalTokensBought);

        require(totalEthDeposited <= ETH_CAP);
        require(totalTokensBought <= TOKEN_CAP);

        viewToken.mint(tokensBought);
        viewToken.transfer(msg.sender, tokensBought);

        LogBuy(msg.sender, msg.value, tokensBought);
    }


    // AUTH REQUIRED //

    function startSale(uint duration, uint blockOffset) auth salePending {
        require(duration > 0);
        require(blockOffset >= 0);

        startBlock = add(block.number, blockOffset);
        endBlock   = add(startBlock, duration);
        state      = State.Running;

        LogStartSale(startBlock, endBlock);
    }

    function endSale() auth saleRunning {
        state = State.Ended;

        LogEndSale(totalEthDeposited, totalTokensBought);
    }

    function extendSale(uint blocks) auth saleRunning {
        require(blocks > 0);

        endBlock += add(endBlock, blocks);
    }

    function collectEth() auth {
        require(this.balance > 0);

        totalEthCollected = add(totalEthCollected, this.balance);
        beneficiary.transfer(this.balance);
    }


    // PRIVATE //

    uint128 constant averageTokensPerEth = wdiv(cast(TOKEN_CAP), cast(ETH_CAP));
    uint128 constant endingTokensPerEth = wdiv(2 * averageTokensPerEth, cast(2 ether + BONUS));

    // calculate number of tokens buyer get when sending 'ethSent' ethers
    // after 'ethDepostiedSoFar` already reeived in the sale
    function calcTokensForPurchase(uint ethSent, uint ethDepositedSoFar)
        private view
        returns (uint128 tokens)
    {
        uint128 tokensPerEthAtStart = calcTokensPerEth(cast(ethDepositedSoFar));
        uint128 tokensPerEthAtEnd = calcTokensPerEth(cast(add(ethDepositedSoFar, ethSent)));
        uint128 averageTokensPerEth = wadd(tokensPerEthAtStart, tokensPerEthAtEnd) / 2;

        // = ethSent * averageTokensPerEthInThisPurchase
        return wmul(cast(ethSent), averageTokensPerEth);
    }

    // return tokensPerEth for 'nthEther' of total contribution (ETH_CAP)
    function calcTokensPerEth(uint128 nthEther)
        private view
        returns (uint128)
    {
        uint128 shareOfSale = wdiv(nthEther, cast(ETH_CAP));
        uint128 shareOfBonus = wsub(1 ether, shareOfSale);
        uint128 actualBonus = wmul(shareOfBonus, cast(BONUS));

        // = endingTokensPerEth * (1 + shareOfBonus * BONUS)
        return wmul(endingTokensPerEth, wadd(1 ether, actualBonus));
    }
}
