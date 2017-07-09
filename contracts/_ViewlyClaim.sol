// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)


// The purpose of this contract is to provide an alternative,
// graudal claiming process, as opposed to the genesis+faucet approach.

// This contract has to be linked to the VIEW ERC-20 Contract,
// copy its state (snapshot), and allow original buyers
// to manage their claims.

pragma solidity ^0.4.11;

import "./lib/math.sol";
import "./lib/token.sol";
import "./lib/note.sol";
import "./lib/auth.sol";


contract ViewlyClaim is DSAuth, DSMath, DSNote {

    address public ViewlySale;
    DSToken public VIEW;

    // future proofing
    struct Claim {
        bytes32 viewlyAddr;
        uint256 amount;
    }
    mapping (address => Claim) public viewlyClaims;
    mapping (bytes32 => address) public reverseViewlyClaims;

    mapping (address => string) public viewlyKeys;


    // mapping (address => bytes32[]) public foo;

    // each viewly address can get coins from multiple ETH addresses,
    // or same address multiple times
    // bytes32 => []Claim
    // bytes32 => address => Claim  :: here we increment deposits in 1:1 relationships
    // each ETH address can reference multiple viewly addresses
    // address => []bytes32


    event LogRegister(
        address user,
        string key
    );

    function ViewlyClaim(DSToken _view) {
        VIEW = _view;
        // assert(VIEW.totalSupply() == 0);
        // assert(VIEW.owner() == address(this));
        // assert(VIEW.authority() == DSAuthority(0));

        // assert that the last Viewly sale has been done
    }

    // ---------------
    // CLAIM FUNCTIONS
    // ---------------

    // Allow token holders to register their Viewly public key.
    // This operation destroys VIEW tokens on Ethereum.
    // Addresses registered here will be included in Viewly genesis, or
    // be claimable at the registration faucet.
    //
    // WARN: This contract is not safe to port to ViewlySaleRecurrent as is,
    // as it would allow for hard cap of 100M to be surpassed due to the
    // burning of the coins.
    function registerAndBurn(bytes32 viewlyAddr, uint256 amountToBurn) note {
        uint256 balance = VIEW.balanceOf(msg.sender);
        assert(balance > 0);
        assert(balance > amountToBurn);
        VIEW.burn(cast(balance));

        // if the user already claimed an amount, add to previous entry
        Claim existingClaim = viewlyClaims[msg.sender];
        if (existingClaim.amount > 0) {
            // don't allow the change of existing address to avoid possible double-issuance
            assert(existingClaim.viewlyAddr == viewlyAddr);

            // add to the old balance
            existingClaim.amount = add(existingClaim.amount, balance);
            viewlyClaims[msg.sender] = existingClaim;
        } else {
            viewlyClaims[msg.sender] = Claim(viewlyAddr, balance);
            reverseViewlyClaims[viewlyAddr] = msg.sender;
        }

    }

    function balanceOfViewlyAddr(bytes32 viewlyAddr) constant returns(uint256) {
        address addr = reverseViewlyClaims[viewlyAddr];
        assert(addr != 0x0);
        return viewlyClaims[addr].amount;
    }

}
