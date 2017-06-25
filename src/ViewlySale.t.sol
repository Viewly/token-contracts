pragma solidity ^0.4.11;

import "ds-test/test.sol";

import "./ViewlySale.sol";

contract ViewlySaleTest is DSTest {
    ViewlySale sale;
    DSToken token;

    function setUp() {
        sale = new ViewlySale();
        //token = new DSToken('VIEW');
        //token.setOwner(sale);
        //sale.initialize(token);
    }

    function test_basic_sanity() {
        assert(true);
    }

    function testFail_basic_sanity() {
        assert(false);
    }

    function testStartSale() {
        uint256 blockFutureOffset = 30;
        uint128 ethUsdPrice = 300;
        sale.startSale(blockFutureOffset, ethUsdPrice);
    }
}
