import pytest

from web3.contract import Contract
from eth_utils import to_wei
from ethereum.tester import TransactionFailed
from populus.chain.base import BaseChain

from helpers import deploy_contract, send_eth


# -------------------
# FIXTURES AND CONSTS
# -------------------

MULTISIG_ADDR = '0x0000000000000000000000000000000000000000'

SALE_ROUNDS = {
    1: {
        'block_future_offset': 0,
        'duration': 10,
        'token_cap': to_wei(100, 'ether'),
        'eth_cap': to_wei(100, 'ether'),
    },
    2: {
        'block_future_offset': 0,
        'duration': 10,
        'token_cap': to_wei(18_000_000, 'ether'),
        'eth_cap': to_wei(18_000_000, 'ether') // 300,  # 1 ETH = $300, 18M USD cap
    }
}

@pytest.fixture()
def view_token(chain: BaseChain) -> Contract:
    """ A blank and running VIEW token contract. """
    return deploy_contract(chain, 'DSToken', args=['VIEW'])

@pytest.fixture()
def viewly_sale(chain: BaseChain, view_token: Contract) -> Contract:
    """ A blank sale contract. """
    viewly_sale = deploy_contract(chain, 'ViewlySale', args=[view_token.address, MULTISIG_ADDR])
    view_token.transact().setOwner(viewly_sale.address)
    return viewly_sale

@pytest.fixture()
def running_round_one(viewly_sale: Contract) -> Contract:
    """
    A blank sale,
    with first round started.
    """
    return step_start_round(viewly_sale)

@pytest.fixture()
def running_round_one_buyers(chain: BaseChain, running_round_one: Contract,
                             web3, customer, customer2) -> Contract:
    """
    A blank sale,
    with first round started,
    with dummy buyers.
    """
    buyers = [customer, customer2]
    return step_make_purchases(chain, running_round_one, web3, buyers)

@pytest.fixture()
def ending_round_one(chain: BaseChain, running_round_one_buyers: Contract) -> Contract:
    """
    A blank sale,
    with first round started,
    with dummy buyers,
    with first round ended.
    """
    return step_end_round(chain, running_round_one_buyers)

@pytest.fixture
def owner(accounts) -> str:
    return accounts[0]

@pytest.fixture
def customer(accounts) -> str:
    return accounts[1]

@pytest.fixture
def customer2(accounts) -> str:
    return accounts[2]


# --------
# TESTS
# --------

def test_init(viewly_sale):
    sale = viewly_sale

    # sanity check, values should be initalized to 0
    assert sale.call().roundNumber() == 0

    # initial supply should be 0
    assert sale.call().totalTokenSupply() == 0

    # state.Pending
    assert sale.call().state() == 0

    # test that the beneficiary account is correct
    assert sale.call().multisigAddr() == MULTISIG_ADDR

    # test token suplly caps
    assert sale.call().tokenCreationCap() == to_wei(1_000_000_000, 'ether')
    assert sale.call().mintMonthlyCap() == to_wei(20_000_000, 'ether')

def test_round_one(ending_round_one):
    # magic happens here ^^
    pass

def test_round_two(ending_round_one, web3, customer, customer2, chain):
    """ Test if additional rounds tally up correctly. """
    sale = ending_round_one
    sale = step_start_round(sale, round_num=2)
    buyers = [customer, customer2]
    sale = step_make_purchases(chain, sale, web3, buyers)
    sale = step_end_round(chain, sale)

    # manual assertions based on hardcoded params in
    # step_start_round and step_make_purchases
    assert sale.call().totalTokenSupply() == 18_000_100 * 10**18
    assert sale.call().totalEthRaised() == to_wei(40, 'ether')
    assert sale.call().ethDeposits(1, customer) == to_wei(10, 'ether')
    assert sale.call().ethDeposits(2, customer) == to_wei(10, 'ether')
    assert sale.call().ethRaisedInRound(1) == to_wei(20, 'ether')
    assert sale.call().ethRaisedInRound(2) == to_wei(20, 'ether')
    assert sale.call().tokenSupplyInRound(1) == 100 * 10**18
    assert sale.call().tokenSupplyInRound(2) == 18_000_000 * 10**18


def test_buyTokens(chain, running_round_one, web3, customer, customer2):
    sale = running_round_one
    roundNumber = sale.call().roundNumber()

    # buying some tokens should work without err
    msg_value = to_wei(10, "ether")
    send_eth(chain, customer, sale.address, msg_value)

    # balances should update correctly
    user_deposit = sale.call().ethDeposits(roundNumber, customer)
    assert user_deposit == msg_value
    assert sale.call().ethRaisedInRound(roundNumber) == msg_value

    # the event should have triggered
    events = sale.pastEvents("LogBuy").get()
    assert len(events) == 1
    e = events[0]["args"]
    assert e["roundNumber"] == roundNumber
    assert e["buyer"] == customer
    assert e["ethSent"] == msg_value

    # make another purchase
    msg_value2 = to_wei(30, "ether")
    send_eth(chain, customer2, sale.address, msg_value2)

    # balances should add up correctly
    user_deposit2 = sale.call().ethDeposits(roundNumber, customer2)
    assert user_deposit2 == msg_value2
    assert sale.call().ethRaisedInRound(roundNumber) == sum([msg_value, msg_value2])

    # make another purchase from re-used account
    send_eth(chain, customer, sale.address, msg_value)

    # balances should update correctly
    user_deposit = sale.call().ethDeposits(roundNumber, customer)
    assert user_deposit == 2 * msg_value

# test buying tokens up to full roundEthCap amount
def test_buyTokens2(chain, running_round_one, web3, customer, customer2):
    sale = running_round_one
    round = sale.call().roundNumber()

    send_eth(chain, customer, sale.address, to_wei(20, "ether"))
    send_eth(chain, customer2, sale.address, to_wei(80, "ether"))

    purchase_1_eth = sale.call().ethDeposits(round, customer)
    purchase_2_eth = sale.call().ethDeposits(round, customer2)
    assert (purchase_1_eth + purchase_2_eth) == to_wei(100, "ether")
    assert sale.call().ethRaisedInRound(round) == to_wei(100, "ether")
    assert sale.call().roundEthCap() == to_wei(100, "ether")

def test_buyTokensFail(chain, viewly_sale, web3, customer):
    sale = viewly_sale

    # sale is not running, so the purchase should fail
    assert is_not_running(viewly_sale)
    try:
        send_eth(chain, customer, sale.address, to_wei(10, "ether"))
        raise AssertionError("Buying tokens on closed sale should have failed")
    except TransactionFailed:
        pass

def test_buyTokensFail2(chain, running_round_one, web3, customer):
    sale = running_round_one
    # is_running(sale)

    # user tries to buy more than available (ETH Cap reached)
    msg_value = to_wei(100000, "ether")
    assert sale.call().roundEthCap() < msg_value
    with pytest.raises(TransactionFailed):
        send_eth(chain, customer, sale.address, msg_value)

def test_claim(ending_round_one, customer):
    sale = ending_round_one

    # sanity checks
    assert sale.call().ethDeposits(1, customer) == to_wei(10, 'ether')
    assert sale.call().tokenSupplyInRound(1) == SALE_ROUNDS[1]['token_cap']
    assert sale.call().ethRaisedInRound(1) == to_wei(20, 'ether')

    # this user sent in 10 eth, should get 50% of token supply
    sale.transact({"from": customer}).claim(1)

    # the new deposit balance should be empty
    assert sale.call().ethDeposits(1, customer) == 0

    # calculate if customer received correct amount of VIEW tokens
    round_eth_raised = sale.call().ethRaisedInRound(1)
    should_receive = to_wei(10, 'ether') * SALE_ROUNDS[1]['token_cap'] // round_eth_raised

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

    multisig_balance = web3.eth.getBalance(MULTISIG_ADDR)
    assert multisig_balance == 0

    contract_balance = web3.eth.getBalance(sale.address)
    assert contract_balance == to_wei(20, 'ether')

    # drain the contract
    sale.transact().secureEth()

    multisig_balance = web3.eth.getBalance(MULTISIG_ADDR)
    assert multisig_balance == to_wei(20, 'ether')

    contract_balance = web3.eth.getBalance(sale.address)
    assert contract_balance == 0


def test_totalEthRaised(running_round_one_buyers):
    sale = running_round_one_buyers

    # by default, running_round_one_buyers will make 2x 10 ETH deposits
    assert sale.call().totalEthRaised() == to_wei(10*2, 'ether')


def test_totalTokenSupply(viewly_sale):
    # start a round
    # make a test purchase
    # end the round
    # claim the tokens
    # issue some reserved tokens
    # call VIEW.totalTokenSupply()
    # call ViewlySale.totalTokenSupply()
    pass


def test_mintReserve(viewly_sale):
    sale = viewly_sale
    to_mint = 10_000

    # sanity checks
    mintable_now = sale.call().mintMonthlyCap() - sale.call().mintedLastMonth()
    assert mintable_now > 0
    # since we haven't minted any tokens previously, the whole
    # monthly allocation should be mintable already
    assert sale.call().mintMonthlyCap() == mintable_now

    # multisig addr should have the newly minted tokens
    balance_before = sale.call().balanceOf(MULTISIG_ADDR)
    sale.transact().mintReserve(to_mint)
    assert sale.call().balanceOf(MULTISIG_ADDR) == balance_before + to_mint

def test_mintedLastMonth(viewly_sale):
    sale = viewly_sale
    assert sale.call().mintedLastMonth() == 0

    to_mint = 10_000
    step_mint_tokens(sale, to_mint)
    assert sale.call().mintedLastMonth() == to_mint


# -------
# HELPERS
# -------

def is_running(sale):
    return sale.call().state() == 1

def is_not_running(sale):
    return sale.call().state() != 1

def step_start_round(sale: Contract, round_num = 1) -> Contract:
    assert is_not_running(sale)

    # start the sale round
    r = SALE_ROUNDS[round_num]
    round_duration = r['duration']
    block_future_offset = r['block_future_offset']
    round_token_cap = r['token_cap']
    round_eth_cap = r['eth_cap']

    sale.transact().startSaleRound(
        round_duration,
        block_future_offset,
        round_token_cap,
        round_eth_cap,
    )

    # state.Running
    assert is_running(sale)

    # check that values were initialized properly
    assert sale.call().roundNumber() == round_num

    # check that the funds were allocated correctly
    roundTokenCap = sale.call().roundTokenCap()
    assert sale.call().tokenSupplyInRound(round_num) == roundTokenCap
    if round_num == 1:
        assert sale.call().totalTokenSupply() == roundTokenCap
    else:
        # if this is a second round, we should have more supply now
        assert sale.call().totalTokenSupply() > roundTokenCap

    # check that the eth Cap is correct
    assert sale.call().roundEthCap() == round_eth_cap

    return sale

def step_make_purchases(
    chain: BaseChain,
    sale: Contract,
    web3,
    buyers: list,
    amounts: list = None) -> Contract:

    assert is_running(sale)

    if not amounts:
        amounts = [to_wei(10, 'ether') for _ in buyers]

    for buyer, amount in zip(buyers, amounts):
        send_eth(chain, buyer, sale.address, amount)

    return sale

def step_end_round(chain: BaseChain, sale: Contract) -> Contract:
    assert is_running(sale)

    # fast-forward chain up to round end block
    chain.wait.for_block(sale.call().roundEndBlock())

    sale.transact().endSaleRound()
    assert is_not_running(sale)

    return sale

def step_mint_tokens(sale, to_mint = 10_000):
    # check old values
    minted_before = sale.call().mintedLastMonth()
    balance_before = sale.call().balanceOf(MULTISIG_ADDR)

    # mint new tokens
    sale.transact().mintReserve(to_mint)
    assert sale.call().balanceOf(MULTISIG_ADDR) == balance_before + to_mint

    # amount should have been recorded properly
    assert sale.call().mintedLastMonth() == minted_before + to_mint
