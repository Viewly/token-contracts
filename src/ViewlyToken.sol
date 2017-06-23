pragma solidity ^0.4.11;

import "ds-math/math.sol";
import "ds-token/token.sol";

contract ViewlyToken {
    address public maintainer;
    // account where the crowdsale funds will be proxied to
    address public constant multisig;
    // uint public creationTime = now;

    DSToken  public  VIEW;
    uint128  public  totalSupply;
    uint128  public  foundersAllocation;

    enum State {
        Pending,
        Running,
        Done
    }

    State public state = State.Pending;


    function ViewlyToken(
        uint     _numberOfDays,
        uint128  _totalSupply,
        uint128  _foundersAllocation,
        string   _foundersKey
    ) {
        maintainer = msg.sender;

        assert(totalSupply > foundersAllocation);
    }

    // fallback function
    function () {

    }


    modifier onlyBy(address _acc) {
        if (acc != msg.sender) throw;
        _;
    }

    function initializeSale() {
        if (state != state.Pending) {
            throw;
        }
    }

    function nextState()
        onlyBy(maintainer)
        returns(bool)
    {
        // we can only iterate trough states once
        if (state == state.Done) return false;
        state = State(uint(state) + 1);
        return true;
    }

    function changeMaintainer(address _new_maintainer)
        onlyBy(maintainer)
        returns(bool)
    {
        maintainer = _new_maintainer;
        return true;
    }
}
