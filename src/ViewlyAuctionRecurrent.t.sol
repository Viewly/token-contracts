// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.11;

import "ds-test/test.sol";
import "ds-exec/exec.sol";


import "./ViewlyAuctionRecurrent.sol";

contract ViewlyAuctionRecurrentTest is DSTest, DSMath {
    ViewlyAuctionRecurrent sale;

    TestUser user1;
    TestUser user2;


    function setUp() {
        sale = new ViewlyAuctionRecurrent();
        user1 = TestUser(sale);
        user2 = TestUser(sale);
    }

    function test_basic_sanity() {
        assert(true);
    }

    function testFail_basic_sanity() {
        assert(false);
    }

    function startSaleStub() {
        uint    saleDurationHours_ = 3 * 24;
        uint256 blockFutureOffset_ = 30;
        uint128 roundTokenCap_ = 1000000; // 1%
        uint128 roundEthCap_ = 10000;     // 10_000 ETH
        sale.startSale(
            saleDurationHours_,
            blockFutureOffset_,
            roundTokenCap_,
            roundEthCap_
        );

        // sale += 1
        assert(sale.roundNumber() == 1);

        // first round should already be pre-allocated
        log_named_uint('totalSupply()', sale.totalSupply());
        assert(sale.totalSupply() > 0);
    }
    function test_startSale() {
        // init sale
        startSaleStub();

        // test that the calculation of block number start, end is correct
        uint blockFutureOffset_ = 30; // same as startSaleStub()
        assert(sale.roundStartBlock() > 0);
        assert(sale.roundEndBlock() > 0);
        uint256 saleDuration = sale.roundEndBlock() - sale.roundStartBlock();
        uint256 supposedSaleDuration = blockFutureOffset_ + sale.roundDurationHours()*mul(div(60, 17), 60);
        uint256 diff = sub(supposedSaleDuration, saleDuration);
        log_named_uint('saleDuration', saleDuration);
        log_named_uint('supposedSaleDuration', supposedSaleDuration);
        log_named_uint('diff', diff);
        assert(diff == blockFutureOffset_);
    }

    function test_buyTokens() {
        // init sale
        startSaleStub();

        assert(sale.totalSupply() == 0);
        sale.buyTokens.value(1 ether)();
        // assert(sale.mapEthDeposits[1][msg.sender] == 1 ether);
        // assert(sale.mapEthSums[1] == 1 ether);
    }

    function test_freeze() {
        sale.freeze();
        // assert(sale.VIEW.stopped());
    }

    function testFail_secureETH() {
        sale.secureETH();
    }

    function test_secureETH() {
        // deposit some funds into contract
        // sale.secureETH();
    }
}

contract TestUser is DSExec {
    ViewlyAuctionRecurrent sale;

    function TestUser(ViewlyAuctionRecurrent sale_) {
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
