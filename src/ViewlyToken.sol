// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.11;

//import "ds-math/math.sol";
//import "ds-token/token.sol";

import "./math.sol";
import "./token.sol";

contract ViewlySale is DSMath {

    // crowdsale owner
    address public maintainer;
    // account where the crowdsale funds will be proxied to
    address public constant multisigAddr = 0x0;  // todo set this

    // supply and allocation
    DSToken public VIEW;
    uint128 public constant tokenCreationCap = 100000000;   // 100_000_000
    uint128 public constant reservedAllocation = 0.2 ether; // 20%


    // crowsdale specs
    uint public constant saleDurationDays = 3;
    uint public constant BLOCKS_PER_DAY = 1234; // todo set this

    // variables calculated on sale start
    uint128 public tokenExchangeRate;  // eg. 1000 VIEW for 1 ETH
    uint256 public fundingStartBlock;  // startSale() block
    uint256 public fundingEndBlock;    // fundingStartBlock + N days


    // state machine
    enum State {
        Pending,
        Running,
        Done
    }
    State public state = State.Pending;

    event Debug(uint256 msg);


    function ViewlyToken(
    //uint128  foundersAllocation_,
    //string   foundersKey_
    ) {
        // set sale contract maintainer
        maintainer = msg.sender;

        // initialize the ERC-20 Token
        VIEW = new DSToken('VIEW');
        assert(VIEW.totalSupply() == 0);

        // mint reserved coins
        // while this implementation is convenient from programming perspective,
        // these tokens should be awarded with each sale, in issueToken()
        // otherwise, reserved allocation will be incorrect in the case
        // where not all tokens are sold
        uint128 reservedTokens = wmul(tokenCreationCap, reservedAllocation);
        VIEW.mint(reservedTokens);
        assert(VIEW.totalSupply() < tokenCreationCap);

    }

    // fallback function
    // triggered when people send ETH directly to this contract
    function () payable {
        issueTokens();
    }


    modifier onlyBy(address _acc) {
        if (_acc != msg.sender) throw;
        _;
    }

    modifier isRunning() {
        if (state != State.Running) throw;
        _;
    }

    function issueTokens() isRunning payable {
        assert(block.number >= fundingStartBlock);
        assert(block.number < fundingEndBlock);
        if (msg.value == 0) throw;

        // calculate the tokens to be allocated
        uint256 tokens = mul(msg.value, tokenExchangeRate);

        // check if the sale is over the cap
        uint256 postSaleSupply = add(VIEW.totalSupply(), tokens);
        if (tokenCreationCap < postSaleSupply) throw;

        // award the tokens
        VIEW.mint(cast(tokens));

        Debug(tokens);
        Debug(VIEW.totalSupply());

    }


    function startSale(
        uint256 blockFutureOffset,
        uint ethUsdPrice
    )
        onlyBy(maintainer)
    {
        // sanity checks
        assert(state == State.Pending);
        // assert(address(VIEW-uninitialized) == address(0));
        assert(VIEW.owner() == address(this));
        assert(VIEW.authority() == DSAuthority(0));

        // the sale can be in Running state before its fundingStartBlock
        // We want to be able to start the sale contract for a block slightly
        // in the future, so that the start time is accurately known
        state = State.Running;
        fundingStartBlock = add(block.number, blockFutureOffset);

        // calculate fundingEndBlock
        // calculate tokenExchangeRate

    }

    function nextState()
        onlyBy(maintainer)
        returns(bool)
    {
        // we can only iterate trough states once
        if (state == State.Done) return false;
        state = State(uint(state) + 1);
        return true;
    }

    function changeMaintainer(address new_maintainer)
        onlyBy(maintainer)
        returns(bool)
    {
        maintainer = new_maintainer;
        return true;
    }
}
