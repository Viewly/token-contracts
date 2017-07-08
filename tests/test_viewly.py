import pytest

@pytest.fixture()
def viewly_sale(chain):
    TokenFactory = chain.get_contract_factory('ViewlyAuctionRecurrent')
    deploy_txn_hash = TokenFactory.deploy()  # arguments=[x, y, z]
    contract_address = chain.wait.for_contract_address(deploy_txn_hash)
    return TokenFactory(address=contract_address)

def test_init(viewly_sale):
    # sanity check, values should be initalized to 0
    assert viewly_sale.call().roundNumber() == 0

    # initial supply should be 0
    assert viewly_sale.call().totalSupply() == 0

    # state.Pending
    assert viewly_sale.call().state() == 0

    # test that the beneficiary account is correct
    addr = '0x0000000000000000000000000000000000000000'
    assert viewly_sale.call().multisigAddr() == addr


def test_startSale(viewly_sale, web3):
    # initialize the sale
    viewly_sale.transact().startSale(
        5 * 24,  # run the sale for 5 days
        0,  # blockFutureOffset
        18_000_000,  # roundTokenCap
        18_000_000 // 245,  # roundEthCap, divided by eth price
    )

    # state.Running
    assert viewly_sale.call().state() == 1

    # check that values were initialized properly
    assert viewly_sale.call().roundNumber() == 1

def test_finalizeSale(viewly_sale):
    pass

def test_totalSupply(viewly_sale):
    pass
