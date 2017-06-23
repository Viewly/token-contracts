pragma solidity ^0.4.11;

import "ds-test/test.sol";

import "./ViewlyToken.sol";

contract ViewlyTokenTest is DSTest {
    ViewlyToken token;

    function setUp() {
        token = new ViewlyToken(10, 1000, 0.1 ether, "0x6fb078e52acdb08a524804307804b4ad1517318e");
    }

    function testFail_basic_sanity() {
        assert(false);
    }

    function test_basic_sanity() {
        assert(true);
    }
}
