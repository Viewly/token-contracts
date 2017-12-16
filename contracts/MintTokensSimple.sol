// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.18;

import "./dappsys/math.sol";
import "./dappsys/token.sol";
import "./dappsys/auth.sol";

/*
   MintTokensSimple is authoried to mint VIEW Tokens for distribution
   within the constraints set in the Viewly Whitepaper.
 */
contract MintTokensSimple is DSAuth, DSMath {

    enum Bucket {
        Founders,
        Supporters,
        Creators,
        Bounties
    }

    struct Category {
        uint categoryLimit;
        uint amountMinted;
    }

    DSToken public viewToken;
    Category[4] public categories;

    event LogPayment(
        address recipient,
        uint tokens,
        Bucket bucket
    );

    function MintTokensSimple(DSToken viewToken_) {
        viewToken = viewToken_;

        uint MILLION = 1000000 ether;
        categories[uint8(Bucket.Founders)]   = Category(18 * MILLION, 0 ether);
        categories[uint8(Bucket.Supporters)] = Category(9 * MILLION, 0 ether);
        categories[uint8(Bucket.Creators)]   = Category(20 * MILLION, 0 ether);
        categories[uint8(Bucket.Bounties)]   = Category(3 * MILLION, 0 ether);
    }

    function mint(address recipient, uint tokens, Bucket bucket) auth {
        require(tokens > 0);
        Category category = categories[uint8(bucket)];
        require(add(tokens, category.amountMinted) <= category.categoryLimit);

        categories[uint8(bucket)].amountMinted += tokens;
        viewToken.mint(recipient, tokens);
        LogPayment(recipient, tokens, bucket);
    }

    function suicide(address addr) auth {
        // this will delete `payments` lookup, so we may want to keep it
        // a better way to kill this contract is to remove its authority
        selfdestruct(addr);
    }
}
