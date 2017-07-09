# The MIT License (MIT)
# Copyright (c) 2017 Viewly (https://view.ly)
import pytest

from web3.contract import Contract
from eth_utils import to_wei

from ethereum.tester import TransactionFailed

multisig_addr = '0x0000000000000000000000000000000000000000'


@pytest.fixture()
def viewly_sale(chain) -> Contract:
    """ A blank sale. """
    TokenFactory = chain.get_contract_factory('ViewlySale')
    deploy_txn_hash = TokenFactory.deploy(args=[True])  # isTestable_=True
    contract_address = chain.wait.for_contract_address(deploy_txn_hash)
    return TokenFactory(address=contract_address)


def step_start_sale(sale: Contract) -> Contract:
    assert is_not_running(sale)

    # initialize the sale
    round_sale_duration = 5 * 24
    block_future_offset = 0
    round_token_cap = 18_000_000
    round_eth_cap = 18_000_000 // 245

    sale.transact().startSale(
        round_sale_duration,
        block_future_offset,
        round_token_cap,
        to_wei(round_eth_cap, 'ether'),
    )

    # state.Running
    assert is_running(sale)

    # check that values were initialized properly
    assert sale.call().roundNumber() == 1

    # check that the funds were allocated correctly
    roundTokenCap = sale.call().roundTokenCap()
    assert sale.call().mapTokenSums(1) == roundTokenCap
    assert sale.call().totalSupply() == roundTokenCap

    # check that the eth Cap is correct
    assert sale.call().roundEthCap() == to_wei(round_eth_cap, "ether")

    return sale


@pytest.fixture()
def running_round_one(viewly_sale: Contract) -> Contract:
    """
    A blank sale,
    with first round started.
    """
    return step_start_sale(viewly_sale)


def step_make_purchases(sale: Contract,
                        web3,
                        buyers: list,
                        amounts: list = None) -> Contract:

    assert is_running(sale)

    if not amounts:
        amounts = [to_wei(10, 'ether') for _ in buyers]

    for buyer, amount in zip(buyers, amounts):
        web3.eth.sendTransaction({
            "from": buyer,
            "to": sale.address,
            "value": amount,
            "gas": 250000,
        })

    return sale

@pytest.fixture()
def running_round_one_buyers(running_round_one: Contract,
                             web3, customer, customer2) -> Contract:
    """
    A blank sale,
    with first round started,
    with dummy buyers.
    """
    buyers = [customer, customer2]
    return step_make_purchases(running_round_one, web3, buyers)



def step_finalize_sale(sale: Contract) -> Contract:
    assert is_running(sale)

    # make the sale close-able
    sale.transact().collapseBlockTimes()
    sale.transact().finalizeSale()

    assert is_not_running(sale)

    return sale

@pytest.fixture()
def ending_round_one(running_round_one_buyers: Contract) -> Contract:
    """
    A blank sale,
    with first round started,
    with dummy buyers,
    with first round ended.
    """
    return step_finalize_sale(running_round_one_buyers)

@pytest.fixture
def beneficiary(accounts) -> str:
    return accounts[0]

@pytest.fixture
def customer(accounts) -> str:
    return accounts[1]

@pytest.fixture
def customer2(accounts) -> str:
    return accounts[2]

def test_init(viewly_sale):
    sale = viewly_sale

    # sanity check, values should be initalized to 0
    assert sale.call().roundNumber() == 0

    # initial supply should be 0
    assert sale.call().totalSupply() == 0

    # state.Pending
    assert sale.call().state() == 0

    # test that the beneficiary account is correct
    assert sale.call().multisigAddr() == multisig_addr


def test_round_one(ending_round_one):
    # the magic happens here ^^
    pass


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

def test_buyTokens(running_round_one, web3, customer, customer2):
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

    # make another purchase
    msg_value2 = to_wei(100, "ether")
    web3.eth.sendTransaction({
        "from": customer2,
        "to": sale.address,
        "value": msg_value2,
        "gas": 250000,
    })

    # balances should add up correctly
    user_deposit2 = sale.call().mapEthDeposits(roundNumber, customer2)
    assert user_deposit2 == msg_value2
    assert sale.call().mapEthSums(roundNumber) == sum([msg_value, msg_value2])

    # make another purchase from re-used account
    web3.eth.sendTransaction({
        "from": customer,
        "to": sale.address,
        "value": msg_value,
        "gas": 250000,
    })

    # balances should update correctly
    user_deposit = sale.call().mapEthDeposits(roundNumber, customer)
    assert user_deposit == 2 * msg_value



def test_finalizeSale(viewly_sale):
    pass

def test_totalSupply(viewly_sale):
    # start a round
    # make a test purchase
    # end the round
    # claim the tokens
    # issue some reserved tokens
    # call VIEW.totalSupply()
    # call ViewlySale.totalSupply()
    pass


# helpers
# -------
def is_running(sale):
    assert sale.call().state() == 1
    return True

def is_not_running(sale):
    assert sale.call().state() != 1
    return True


# ViewlySale.isTesting
# --------------------
def test_testing_methods_unavailable(chain):
    """ Testing helpers should not be callable
    in a production like deployment. """

    # production like contract
    TokenFactory = chain.get_contract_factory('ViewlySale')
    deploy_txn_hash = TokenFactory.deploy(args=[False])  # isTestable_=False
    contract_address = chain.wait.for_contract_address(deploy_txn_hash)
    sale = TokenFactory(address=contract_address)

    # initialize the sale
    sale = step_start_sale(sale)
    assert is_running(sale)

    # calling a test protected method should fail
    with pytest.raises(TransactionFailed):
        sale.transact().collapseBlockTimes()
