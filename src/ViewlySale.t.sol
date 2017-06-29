pragma solidity ^0.4.11;

import "ds-test/test.sol";
import "ds-exec/exec.sol";


import "./ViewlySale.sol";

contract ViewlySaleTest is DSTest, DSMath {
    ViewlySale sale;

    TestUser user1;
    TestUser user2;


    function setUp() {
        sale = new ViewlySale();
        user1 = TestUser(sale);
        user2 = TestUser(sale);
    }

    function test_basic_sanity() {
        assert(true);
    }

    function testFail_basic_sanity() {
        assert(false);
    }

    function test_startSale() {
        uint256 blockFutureOffset = 30;
        uint128 ethUsdPrice = 300;
        uint saleDurationHours_ = 3 * 24;
        sale.startSale(saleDurationHours_, blockFutureOffset, ethUsdPrice);

        // test that the calculation of block number start, end is correct
        assert(sale.fundingStartBlock() > 0);
        assert(sale.fundingEndBlock() > 0);
        uint256 saleDuration = sale.fundingEndBlock() - sale.fundingStartBlock();
        uint256 supposedSaleDuration = blockFutureOffset + sale.saleDurationHours()*mul(div(60, 17), 60);
        uint256 diff = sub(supposedSaleDuration, saleDuration);
        log_named_uint('saleDuration', saleDuration);
        log_named_uint('supposedSaleDuration', supposedSaleDuration);
        log_named_uint('diff', diff);
        assert(diff == blockFutureOffset);

        // test that the token exchange rate is correct
        assert(wmul(wdiv(sale.maxTokensForSale(), sale.tokenExchangeRate()), ethUsdPrice) == sale.usdSaleCap());
    }

    function test_finalizeSale() {
        sale.endSaleStub();
    }

    // paying after the sale ended should fail
    function testFail_finalizeSale() {
        sale.endSaleStub();
        sale.buyTokens.value(1 ether)();
    }

    function test_buyTokens() {
        uint256 blockFutureOffset = 0;
        uint128 ethUsdPrice = 300;
        uint saleDurationHours_ = 3 * 24;
        sale.startSale(saleDurationHours_, blockFutureOffset, ethUsdPrice);

        assert(sale.totalSupply() == 0);
        sale.buyTokens.value(1 ether)();
        log_named_uint('totalSupply()', sale.totalSupply());
        assert(sale.totalSupply() > 0);
//        user1.doBuy(1 ether);
    }

    function test_calcReservedSupply() {
        sale.calcReservedSupply();
    }

    function test_freeze() {
        sale.freeze();
//        assert(sale.VIEW.stopped());
    }

    function testFail_secureETH() {
        sale.secureETH();
    }

    function test_secureETH() {
        // deposit some funds into contract
//        sale.secureETH();
    }
}

contract TestUser is DSExec {
    ViewlySale sale;

    function TestUser(ViewlySale sale_) {
        sale = sale_;
    }

    function() payable {}

    function doBuy(uint wad) {
        sale.buyTokens.value(wad)();
    }

    function doExec(uint wad) {
        exec(sale, wad);
    }
}
