// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.18;

import "./dappsys/math.sol";
import "./dappsys/token.sol";
import "./dappsys/auth.sol";

/*
   ViewlyTokensMintage contract is used to mint VIEW Tokens within the
   constraints set in the Viewly Whitepaper. It tracks total minted tokens for
   each distribution category.
 */
contract ViewlyTokensMintage is DSAuth, DSMath {

    enum CategoryId {
        Founders,
        Supporters,
        Creators,
        Bounties
    }

    struct Category {
        uint mintLimit;
        uint amountMinted;
    }

    DSToken public viewToken;
    Category[4] public categories;

    event TokensMinted(
        address recipient,
        uint tokens,
        CategoryId category
    );

    function ViewlyTokensMintage(DSToken viewToken_) {
        viewToken = viewToken_;

        uint MILLION = 1000000 ether;
        categories[uint8(CategoryId.Founders)]   = Category(18 * MILLION, 0 ether);
        categories[uint8(CategoryId.Supporters)] = Category(9 * MILLION, 0 ether);
        categories[uint8(CategoryId.Creators)]   = Category(20 * MILLION, 0 ether);
        categories[uint8(CategoryId.Bounties)]   = Category(3 * MILLION, 0 ether);
    }

    function mint(address recipient, uint tokens, CategoryId categoryId) auth {
        require(tokens > 0);
        Category category = categories[uint8(categoryId)];
        require(add(tokens, category.amountMinted) <= category.mintLimit);

        categories[uint8(categoryId)].amountMinted += tokens;
        viewToken.mint(recipient, tokens);
        TokensMinted(recipient, tokens, categoryId);
    }

    /* Selfdestruct action should be coupled with removal of this
       version of ViewlyTokensMintage from View token authority.
     */
    function selfdestruct(address addr) auth {
        selfdestruct(addr);
    }
}
