// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.16;

import "./lib/math.sol";
import "./lib/token.sol";
import "./lib/auth.sol";

// Viewly seed token sale contract
contract ViewlySeedSale is DSAuth, DSMath {

    uint constant public ethCap   =         4000 ether;   // ether hard-cap
    uint constant public tokenCap = 10 * 1000000 ether;   // token hard-cap

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

    // deposited ethers can be collected any time
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
      // update deposits and tokens bought
      ethDeposits[msg.sender] = add(msg.value, ethDeposits[msg.sender]);
      totalEthDeposited = add(msg.value, totalEthDeposited);
      uint128 tokensBought = calculateTokensFor(msg.value);
      totalTokensBought = add(tokensBought, totalTokensBought);

      // check caps are respected
      require(totalEthDeposited <= ethCap);
      require(totalTokensBought <= tokenCap);

      // return tokens
      VIEW.mint(tokensBought);
      VIEW.transfer(msg.sender, tokensBought);

      LogBuy(msg.sender, msg.value, tokensBought);
    }

    function () payable {
      buyTokens();
    }


    // PRIVATE FUNCTIONS //

    function calculateTokensFor(uint ethSent)
    private constant returns(uint128 tokens)
    {
      // ethSent / ethCap * tokenCap
      return cast(div(mul(ethSent, tokenCap), ethCap));
    }
}
