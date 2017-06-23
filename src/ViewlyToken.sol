pragma solidity ^0.4.11;

//import "ds-math/math.sol";
//import "ds-token/token.sol";

import "./math.sol";
import "./token.sol";

contract ViewlyToken is DSMath {

    // money
    address public maintainer;
    // account where the crowdsale funds will be proxied to
    address public constant multisigAddr = 0x0;  // todo fix this

    // supply
    DSToken public VIEW;
    uint128 public totalSupply = 0x0;   // we don't pre-mine any tokens
    uint128 public foundersAllocation;  // something like 0.2 ether for 20%


    // sale variables, calculated on sale start
    uint128 public tokenExchangeRate;
    uint128 public tokenCreationCap;
    uint public saleStartTime;


    enum State {
        Pending,
        Running,
        Done
    }

    State public state = State.Pending;


    function ViewlyToken(
    //uint     _numberOfDays,
    //uint128  _totalSupply,
    //uint128  _foundersAllocation,
    //string   _foundersKey
    ) {
        maintainer = msg.sender;

        // handle supply
        tokenCreationCap = 100000000; // 100_000_000
        foundersAllocation = wmul(totalSupply, 0.2 ether);
        assert(totalSupply > foundersAllocation);


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

    function issueTokens() isRunning {

    }


    function startSale(uint ethUsdPrice) {
        if (state != State.Pending) {
            throw;
        }
        saleStartTime = now;
        state = State.Running;
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
