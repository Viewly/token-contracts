pragma solidity ^0.4.11;

import "ds-test/test.sol";

import "./ViewlyToken.sol";

contract ViewlyTokenTest is DSTest {
    ViewlyToken token;

    function setUp() {
        token = new ViewlyToken();
    }

    function testFail_basic_sanity() {
        assert(false);
    }

    function test_basic_sanity() {
        assert(true);
    }
}
