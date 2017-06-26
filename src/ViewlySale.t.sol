pragma solidity ^0.4.11;

import "ds-test/test.sol";
import "ds-exec/exec.sol";


import "./ViewlySale.sol";

contract ViewlySaleTest is DSTest, DSMath {
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

    function test_startSale() {
        uint256 blockFutureOffset = 30;
        uint128 ethUsdPrice = 300;
        sale.startSale(blockFutureOffset, ethUsdPrice);

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

    }

    function test_buyTokens() {

    }

    function test_calcReservedSupply() {

    }
}
