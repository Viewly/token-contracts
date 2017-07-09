import pytest

from web3.contract import Contract
from eth_utils import to_wei

from ethereum.tester import TransactionFailed

@pytest.fixture()
def viewly_sale(chain) -> Contract:
    TokenFactory = chain.get_contract_factory('ViewlySale')
    deploy_txn_hash = TokenFactory.deploy()  # arguments=[x, y, z]
    contract_address = chain.wait.for_contract_address(deploy_txn_hash)
    return TokenFactory(address=contract_address)

@pytest.fixture()
def running_round_one(viewly_sale) -> Contract:
    # initialize the sale
    round_sale_duration = 5 * 24
    block_future_offset = 0
    round_token_cap = 18_000_000
    round_eth_cap = 18_000_000 // 245

    viewly_sale.transact().startSale(
        round_sale_duration,
        block_future_offset,
        round_token_cap,
        to_wei(round_eth_cap, 'ether'),
    )

    # state.Running
    is_running(viewly_sale)

    # check that values were initialized properly
    assert viewly_sale.call().roundNumber() == 1

    # check that the funds were allocated correctly
    roundTokenCap = viewly_sale.call().roundTokenCap()
    assert viewly_sale.call().mapTokenSums(1) == roundTokenCap
    assert viewly_sale.call().totalSupply() == roundTokenCap

    # check that the eth Cap is correct
    assert viewly_sale.call().roundEthCap() == to_wei(round_eth_cap, "ether")

    return viewly_sale

# todo:
# fixture endingRound1
# fixture with stub sales
# fixture running_round_two inherits from ended round 1

@pytest.fixture
def customer(accounts) -> str:
    return accounts[1]

@pytest.fixture
def beneficiary(accounts) -> str:
    return accounts[3]

def test_init(viewly_sale):
    sale = viewly_sale

    # sanity check, values should be initalized to 0
    assert sale.call().roundNumber() == 0

    # initial supply should be 0
    assert sale.call().totalSupply() == 0

    # state.Pending
    assert sale.call().state() == 0

    # test that the beneficiary account is correct
    addr = '0x0000000000000000000000000000000000000000'
    assert sale.call().multisigAddr() == addr


def test_buyTokensFail(viewly_sale, web3, customer):
    sale = viewly_sale

    # sale is not running, so the purchase should fail
    is_not_running(viewly_sale)
    try:
        web3.eth.sendTransaction({
            "from": customer,
            "to": sale.address,
            "value": to_wei(10, "ether"),
            "gas": 250000,
        })
        raise AssertionError(
            "Buying tokens on closed sale should have failed")
    except TransactionFailed:
        pass

def test_buyTokensFail2(running_round_one, web3, customer):
    sale = running_round_one
    # is_running(sale)

    # user tries to buy more than available (ETH Cap reached)
    msg_value = to_wei(100000, "ether")
    assert sale.call().roundEthCap() < msg_value
    with pytest.raises(TransactionFailed):
        web3.eth.sendTransaction({
            "from": customer,
            "to": sale.address,
            "value": msg_value,
            "gas": 250000,
        })

def test_buyTokens(running_round_one, web3, customer):
    sale = running_round_one
    roundNumber = sale.call().roundNumber()

    # buying some tokens should work without err
    msg_value = to_wei(10, "ether")
    web3.eth.sendTransaction({
        "from": customer,
        "to": sale.address,
        "value": msg_value,
        "gas": 250000,
    })

    # balances should update correctly
    user_deposit = sale.call().mapEthDeposits(roundNumber, customer)
    assert user_deposit == msg_value
    assert sale.call().mapEthSums(roundNumber) == msg_value

    # the event should have triggered
    events = sale.pastEvents("LogBuy").get()
    assert len(events) == 1
    e = events[0]["args"]
    assert e["roundNumber"] == roundNumber
    assert e["buyer"] == customer
    assert e["ethSent"] == msg_value


def test_startSale(running_round_one, web3):
    pass

def test_finalizeSale(viewly_sale):
    pass

def test_totalSupply(viewly_sale):
    pass


# helpers
# -------
def is_running(sale):
    assert sale.call().state() == 1

def is_not_running(sale):
    assert sale.call().state() != 1
