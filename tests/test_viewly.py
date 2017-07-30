# The MIT License (MIT)
# Copyright (c) 2017 Viewly (https://view.ly)
import pytest

from web3.contract import Contract
from eth_utils import to_wei

from ethereum.tester import TransactionFailed

multisig_addr = '0x0000000000000000000000000000000000000000'

rounds = {
    1: {
        'block_future_offset': 0,
        'duration': 5 * 24 * 3600 // 17,
        'token_cap': 18_000_000,
        'eth_cap': 18_000_000 // 300,  # 1 ETH = $300, 18M USD cap
    },
    2: {
        'block_future_offset': 0,
        'duration': 5 * 24 * 3600 // 17,
        'token_cap': 18_000_000,
        'eth_cap': 18_000_000 // 300,  # 1 ETH = $300, 18M USD cap
    }
}


@pytest.fixture()
def viewly_sale(chain) -> Contract:
    """ A blank sale. """
    TokenFactory = chain.get_contract_factory('ViewlySale')
    deploy_txn_hash = TokenFactory.deploy(args=[multisig_addr, True])  # isTestable_=True
    contract_address = chain.wait.for_contract_address(deploy_txn_hash)
    return TokenFactory(address=contract_address)


def step_start_sale(sale: Contract, round_num = 1) -> Contract:
    assert is_not_running(sale)

    # initialize the sale
    r = rounds[round_num]
    round_sale_duration = r['duration']
    block_future_offset = r['block_future_offset']
    round_token_cap = r['token_cap']
    round_eth_cap = r['eth_cap']

    sale.transact().startSale(
        round_sale_duration,
        block_future_offset,
        round_token_cap,
        to_wei(round_eth_cap, 'ether'),
    )

    # state.Running
    assert is_running(sale)

    # check that values were initialized properly
    assert sale.call().roundNumber() == round_num

    # check that the funds were allocated correctly
    roundTokenCap = sale.call().roundTokenCap()
    assert sale.call().mapTokenSums(round_num) == roundTokenCap
    if round_num == 1:
        assert sale.call().totalSupply() == roundTokenCap
    else:
        # if this is a second round, we should have more supply now
        assert sale.call().totalSupply() > roundTokenCap

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
def owner(accounts) -> str:
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
    # magic happens here ^^
    pass

def test_round_two(ending_round_one, web3, customer, customer2):
    """ Test if additional rounds tally up correctly. """
    sale = ending_round_one
    sale = step_start_sale(sale, round_num=2)
    buyers = [customer, customer2]
    sale = step_make_purchases(sale, web3, buyers)
    sale = step_finalize_sale(sale)

    # manual assertions based on hardcoded params in
    # step_start_sale and step_make_purchases
    assert sale.call().totalSupply() == 2 * 18_000_000
    assert sale.call().totalEth() == to_wei(40, 'ether')
    assert sale.call().mapEthDeposits(1, customer) == to_wei(10, 'ether')
    assert sale.call().mapEthDeposits(2, customer) == to_wei(10, 'ether')
    assert sale.call().mapEthSums(1) == to_wei(20, 'ether')
    assert sale.call().mapEthSums(2) == to_wei(20, 'ether')
    assert sale.call().mapTokenSums(1) == 18_000_000
    assert sale.call().mapTokenSums(2) == 18_000_000


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


def test_claim(ending_round_one, customer):
    sale = ending_round_one

    # sanity checks
    assert sale.call().mapEthDeposits(1, customer) == to_wei(10, 'ether')
    assert sale.call().mapTokenSums(1) == rounds[1]['token_cap']
    assert sale.call().mapEthSums(1) == to_wei(20, 'ether')

    # this user sent in 10 eth, should get 50% of token supply
    sale.transact({"from": customer}).claim(1)

    # the new deposit balance should be empty
    assert sale.call().mapEthDeposits(1, customer) == 0

    # calculate if customer received correct amount of VIEW tokens
    round_eth_raised = sale.call().mapEthSums(1)
    should_receive = to_wei(10, 'ether') / round_eth_raised * rounds[1]['token_cap']
    assert sale.call().balanceOf(customer) == should_receive


def test_claimFail(ending_round_one, customer, owner):
    sale = ending_round_one

    # should not be able to claim 0 round
    with pytest.raises(TransactionFailed):
        sale.transact({"from": customer}).claim(0)

    # should not be able to claim nonexistent round
    with pytest.raises(TransactionFailed):
        sale.transact({"from": customer}).claim(2)

    # should not be able to claim if haven't contributed
    with pytest.raises(TransactionFailed):
        sale.transact({"from": owner}).claim(1)

    # should not be able to claim twice
    sale.transact({"from": customer}).claim(1)
    with pytest.raises(TransactionFailed):
        sale.transact({"from": customer}).claim(1)

def test_secureEth(ending_round_one, web3):
    sale = ending_round_one

    multisig_balance = web3.eth.getBalance(multisig_addr)
    assert multisig_balance == 0

    contract_balance = web3.eth.getBalance(sale.address)
    assert contract_balance == to_wei(20, 'ether')

    # drain the contract
    sale.transact().secureEth()

    multisig_balance = web3.eth.getBalance(multisig_addr)
    assert multisig_balance == to_wei(20, 'ether')

    contract_balance = web3.eth.getBalance(sale.address)
    assert contract_balance == 0


def test_totalEth(running_round_one_buyers):
    sale = running_round_one_buyers

    # by default, running_round_one_buyers will make 2x 10 ETH deposits
    assert sale.call().totalEth() == to_wei(10*2, 'ether')


def test_totalSupply(viewly_sale):
    # start a round
    # make a test purchase
    # end the round
    # claim the tokens
    # issue some reserved tokens
    # call VIEW.totalSupply()
    # call ViewlySale.totalSupply()
    pass


def test_mintableTokenSupply(viewly_sale):
    """ Check that we can really only mint 2% a month. """
    sale = viewly_sale
    hard_cap = sale.call().tokenCreationCap()
    mintMonthlyMax = sale.call().mintMonthlyMax()

    mintable_now = sale.call().mintableTokenAmount()
    assert mintable_now == hard_cap * mintMonthlyMax // 100


def step_mint_tokens(sale, to_mint = 10_000):
    # check old values
    minted_before = sale.call().mintedLastMonthSum()
    balance_before = sale.call().balanceOf(multisig_addr)

    # mint new tokens
    sale.transact().mintReserve(to_mint)
    assert sale.call().balanceOf(multisig_addr) == balance_before + to_mint

    # amount should have been recorded properly
    assert sale.call().mintedLastMonthSum() == minted_before + to_mint

def test_mintReserve(viewly_sale):
    sale = viewly_sale
    to_mint = 10_000

    # sanity checks
    mintableTokenAmount = sale.call().mintableTokenAmount()
    mintable_now = mintableTokenAmount - sale.call().mintedLastMonthSum()
    assert mintable_now > 0
    # since we haven't minted any tokens previously, the whole
    # monthly allocation should be mintable already
    assert sale.call().mintableTokenAmount() == mintable_now

    # multisig addr should have the newly minted tokens
    balance_before = sale.call().balanceOf(multisig_addr)
    sale.transact().mintReserve(to_mint)
    assert sale.call().balanceOf(multisig_addr) == balance_before + to_mint

def test_mintedLastMonthSum(viewly_sale):
    sale = viewly_sale
    assert sale.call().mintedLastMonthSum() == 0

    to_mint = 10_000
    step_mint_tokens(sale, to_mint)
    assert sale.call().mintedLastMonthSum() == to_mint


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
    deploy_txn_hash = TokenFactory.deploy(args=[multisig_addr, False])  # isTestable_=False
    contract_address = chain.wait.for_contract_address(deploy_txn_hash)
    sale = TokenFactory(address=contract_address)

    # initialize the sale
    sale = step_start_sale(sale)
    assert is_running(sale)

    # calling a test protected method should fail
    with pytest.raises(TransactionFailed):
        sale.transact().collapseBlockTimes()
