// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.18;

import "./dappsys/math.sol";
import "./dappsys/token.sol";
import "./dappsys/auth.sol";

/*
 * ViewlyTokenMintage contract is used to mint VIEW Tokens within the
 * constraints set in the Viewly Whitepaper. It tracks total minted tokens for
 * each distribution category.
 */
contract ViewlyTokenMintage is DSAuth, DSMath {

    enum CategoryId {
        Founders,
        Supporters,
        Creators,
        Bounties,
        SeedSale,
        MainSale
    }

    struct Category {
        uint mintLimit;
        uint amountMinted;
    }

    DSToken public viewToken;
    Category[6] public categories;

    event TokensMinted(
        address recipient,
        uint tokens,
        CategoryId category
    );

    function ViewlyTokenMintage(DSToken viewToken_) {
        viewToken = viewToken_;

        uint MILLION = 1000000 ether;
        categories[uint8(CategoryId.Founders)]   = Category(18 * MILLION, 0 ether);
        categories[uint8(CategoryId.Supporters)] = Category(9 * MILLION, 0 ether);
        categories[uint8(CategoryId.Creators)]   = Category(20 * MILLION, 0 ether);
        categories[uint8(CategoryId.Bounties)]   = Category(3 * MILLION, 0 ether);
        categories[uint8(CategoryId.SeedSale)]   = Category(10 * MILLION, 10 * MILLION);
        categories[uint8(CategoryId.MainSale)]   = Category(40 * MILLION, 0 ether);
    }

    function mint(address recipient, uint tokens, CategoryId categoryId) auth {
        require(tokens > 0);
        Category category = categories[uint8(categoryId)];
        require(add(tokens, category.amountMinted) <= category.mintLimit);

        categories[uint8(categoryId)].amountMinted += tokens;
        viewToken.mint(recipient, tokens);
        TokensMinted(recipient, tokens, categoryId);
    }

    function destruct(address addr) auth {
        selfdestruct(addr);
    }
}
