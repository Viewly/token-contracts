pragma solidity ^0.4.11;

import "ds-test/test.sol";

import "./ViewlySale.sol";

contract ViewlySaleTest is DSTest {
    ViewlySale token;

    function setUp() {
        token = new ViewlySale();
    }

    function testFail_basic_sanity() {
        assert(false);
    }

    function test_basic_sanity() {
        assert(true);
    }
}
