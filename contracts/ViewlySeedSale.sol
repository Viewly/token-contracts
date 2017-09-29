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

    uint constant public ethCap   =         4000 ether;   // ether hard-cap
    uint constant public tokenCap = 10 * 1000000 ether;   // token hard-cap
    uint constant public bonus    =         0.15 ether;   // bonus of tokens early buyers
                                                          // get over last buyers

    DSToken public VIEW;              // VIEW token contract
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


    function ViewlySeedSale(DSToken _view, address _beneficiary) {
        VIEW = _view;
        beneficiary = _beneficiary;
    }

    // AUTHORIZATION REQUIRED //

    function startSale(
      uint _duration,
      uint _blockOffset
    ) auth salePending {
        require(_duration > 0);
        require(_blockOffset >= 0);

        startBlock = add(block.number, _blockOffset);
        endBlock   = add(startBlock, _duration);
        state      = State.Running;

        LogStartSale(startBlock, endBlock);
    }

    function endSale() auth saleRunning {
      state = State.Ended;

      LogEndSale(totalEthDeposited, totalTokensBought);
    }

    function extendSale(uint _blocks) auth saleRunning {
      require(_blocks > 0);

      endBlock += add(endBlock, _blocks);
    }

    function collectEth() auth {
      require(this.balance > 0);

      totalEthCollected = add(totalEthCollected, this.balance);
      beneficiary.transfer(this.balance);
    }


    // PUBLIC FUNCTIONS //

    function totalEthRaised() returns(uint) {
      return add(this.balance, totalEthCollected);
    }

    function buyTokens() saleRunning inRunningBlock ethSent payable {
      uint128 tokensBought = calcTokensForPurchase(msg.value, totalEthDeposited);
      ethDeposits[msg.sender] = add(msg.value, ethDeposits[msg.sender]);
      totalEthDeposited = add(msg.value, totalEthDeposited);
      totalTokensBought = add(tokensBought, totalTokensBought);

      require(totalEthDeposited <= ethCap);
      require(totalTokensBought <= tokenCap);

      VIEW.mint(tokensBought);
      VIEW.transfer(msg.sender, tokensBought);

      LogBuy(msg.sender, msg.value, tokensBought);
    }

    function () payable {
      buyTokens();
    }


    // PRIVATE //

    uint128 constant averageTokensPerEth = wdiv(cast(tokenCap), cast(ethCap));
    uint128 constant endingTokensPerEth = wdiv(2 * averageTokensPerEth, cast(2 ether + bonus));

    // calculate number of tokens buyer get when sending 'ethSent' ethers
    // after 'ethDepostiedSoFar` already reeived in the sale
    function calcTokensForPurchase(uint ethSent, uint ethDepositedSoFar)
        private
        constant
        returns (uint128 tokens)
    {
        uint128 tokensPerEthAtStart = calcTokensPerEth(cast(ethDepositedSoFar));
        uint128 tokensPerEthAtEnd = calcTokensPerEth(cast(add(ethDepositedSoFar, ethSent)));
        uint128 averageTokensPerEth = wadd(tokensPerEthAtStart, tokensPerEthAtEnd) / 2;

        // = ethSent * averageTokensPerEthInThisPurchase
        return wmul(cast(ethSent), averageTokensPerEth);
    }

    // return tokensPerEth for 'nthEther' of total contribution (ethCap)
    function calcTokensPerEth(uint128 nthEther)
        private
        constant
        returns (uint128)
    {
        uint128 shareOfSale = wdiv(nthEther, cast(ethCap));
        uint128 shareOfBonus = wsub(1 ether, shareOfSale);
        uint128 currentBonus = wmul(shareOfBonus, cast(bonus));

        // = endingTokensPerEth * (1 + bonus * shareOfBonus)
        return wmul(endingTokensPerEth, wadd(1 ether, currentBonus));
    }
}
