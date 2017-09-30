import pytest

from pytest import approx
from web3.contract import Contract
from eth_utils import to_wei

from ethereum.tester import TransactionFailed
from populus.chain.base import BaseChain


TOKEN_CAP       = to_wei(10000000, 'ether')
ETH_CAP         = to_wei(4000, 'ether')
DURATION        = 10
BLOCK_OFFSET    = 2

def deploy_contract(chain: BaseChain, contract_name: str, args=[]) -> Contract:
    # deploy contract on chain with coinbase and optional init args
    factory = chain.get_contract_factory(contract_name)
    deploy_tx_hash = factory.deploy(args=args)
    contract_address = chain.wait.for_contract_address(deploy_tx_hash)
    return factory(address=contract_address)

def send_eth_to_sale(chain, sale, user, eth_to_send):
    return chain.web3.eth.sendTransaction({
        'from': user,
        'to': sale.address,
        'value': eth_to_send,
        'gas': 250000,
    })

def assert_last_buy_event(sale, eth_sent, tokens_bought, customer=None):
    event = sale.pastEvents('LogBuy').get()[-1]['args']
    assert event['ethDeposit'] == eth_sent
    assert event['tokensBought'] == approx(tokens_bought)
    if customer:
        assert event['buyer'] == customer

@pytest.fixture()
def token(chain: BaseChain) -> Contract:
    """ A VIEW token contract. """
    return deploy_contract(chain, 'DSToken', args=['VIEW'])

@pytest.fixture()
def sale(chain: BaseChain, token: Contract, beneficiary) -> Contract:
    """ A blank ViewlySeedSale contract. """
    args = [token.address, beneficiary]
    seed_sale = deploy_contract(chain, 'ViewlySeedSale', args=args)
    token.transact().setOwner(seed_sale.address)
    return seed_sale

@pytest.fixture()
def running_sale(chain: BaseChain, token: Contract, sale) -> Contract:
    """ A running ViewlySeedSale contract. """
    sale.transact().startSale(DURATION, BLOCK_OFFSET)
    chain.wait.for_block(sale.call().startBlock())
    return sale

@pytest.fixture
def owner(accounts) -> str:
    return accounts[0]

@pytest.fixture
def customer(accounts) -> str:
    return accounts[1]

@pytest.fixture
def customer2(accounts) -> str:
    return accounts[2]

@pytest.fixture
def beneficiary(accounts) -> str:
    return accounts[3]


# --------
# TESTS
# --------

def test_init(chain, token, beneficiary):
    sale = deploy_contract(chain, 'ViewlySeedSale', args=[token.address, beneficiary])

    assert sale.call().viewToken() == token.address
    assert sale.call().beneficiary() == beneficiary

def test_start_sale(web3, sale):
    sale.transact().startSale(DURATION, BLOCK_OFFSET)
    expected_start_block = web3.eth.blockNumber + BLOCK_OFFSET
    expected_end_block = web3.eth.blockNumber + BLOCK_OFFSET + DURATION

    assert sale.call().state() == 1
    assert sale.call().ETH_CAP() == ETH_CAP
    assert sale.call().TOKEN_CAP() == TOKEN_CAP
    assert sale.call().startBlock() == expected_start_block
    assert sale.call().endBlock() == expected_end_block

    start_event = sale.pastEvents('LogStartSale').get()[0]['args']
    assert start_event['startBlock'] == expected_start_block
    assert start_event['endBlock'] == expected_end_block

def test_end_sale(chain: BaseChain, running_sale, customer, beneficiary):
    sale = running_sale
    send_eth_to_sale(chain, sale, customer, ETH_CAP)

    sale.transact().endSale()

    assert sale.call().state() == 2
    end_event = sale.pastEvents('LogEndSale').get()[0]['args']
    assert end_event['totalEthDeposited'] == ETH_CAP
    assert end_event['totalTokensBought'] == approx(TOKEN_CAP)

def test_collect_eth_and_total_eth_raised(chain: BaseChain, running_sale, customer, beneficiary):
    sale = running_sale

    # buy some token on sale
    send_eth_to_sale(chain, sale, customer, to_wei(10, 'ether'))

    # collect deposited eth before end of sale
    start_balance = chain.web3.eth.getBalance(beneficiary)
    sale.transact().collectEth()
    end_balance = chain.web3.eth.getBalance(beneficiary)
    assert (end_balance - start_balance) == to_wei(10, 'ether')
    assert chain.web3.eth.getBalance(sale.address) == 0

    # buy some more
    send_eth_to_sale(chain, sale, customer, to_wei(30, 'ether'))
    assert chain.web3.eth.getBalance(sale.address) == to_wei(30, 'ether')
    assert sale.call().totalEthRaised() == to_wei(40, 'ether')

def test_buy(chain, web3, token, sale, customer):
    sale.transact().startSale(DURATION, 0)

    eth_sent = ETH_CAP
    expected_tokens = TOKEN_CAP
    send_eth_to_sale(chain, sale, customer, eth_sent)

    # sale contract should save eth deposit and update totals
    assert sale.call().ethDeposits(customer) == eth_sent
    assert web3.eth.getBalance(sale.address) == eth_sent
    assert sale.call().totalEthDeposited() == eth_sent

    # token supply should increase
    assert token.call().totalSupply() == approx(expected_tokens)
    # customer should receive expected tokens
    assert token.call().balanceOf(customer) == approx(expected_tokens)

    assert_last_buy_event(sale, ETH_CAP, TOKEN_CAP, customer)

def test_buy_multiple_times_with_bonuses(chain: BaseChain, running_sale, customer):
    sale = running_sale
    half_eth_cap = to_wei(2000, 'ether')

    send_eth_to_sale(chain, sale, customer, half_eth_cap)
    assert_last_buy_event(sale, half_eth_cap, to_wei(5174418.605, 'ether'), customer)

    send_eth_to_sale(chain, sale, customer, half_eth_cap)
    assert_last_buy_event(sale, half_eth_cap, to_wei(4825581.395, 'ether'), customer)

    assert sale.call().totalEthDeposited() == ETH_CAP
    assert sale.call().totalTokensBought() == approx(TOKEN_CAP)

def test_buy_multiple_in_diverse_amounts(chain: BaseChain, running_sale, customer):
    sale = running_sale

    send_eth_to_sale(chain, sale, customer, to_wei(111, 'milli'))
    assert_last_buy_event(sale, to_wei(111, 'milli'), to_wei(296.8599279, 'ether'))

    send_eth_to_sale(chain, sale, customer, to_wei(2322, 'ether'))
    assert_last_buy_event(sale, to_wei(2322, 'ether'), to_wei(5974875.023, 'ether'))

    send_eth_to_sale(chain, sale, customer, to_wei(45, 'ether'))
    assert_last_buy_event(sale, to_wei(45, 'ether'), to_wei(111147.6022, 'ether'))

    send_eth_to_sale(chain, sale, customer, to_wei(1632889, 'milli'))
    assert_last_buy_event(sale, to_wei(1632889, 'milli'), to_wei(3913680.515, 'ether'))

    assert sale.call().totalEthDeposited() == ETH_CAP
    assert sale.call().totalTokensBought() == approx(TOKEN_CAP)

def test_extend_sale(chain: BaseChain, token, running_sale, customer):
    sale = running_sale

    # buying something on end block should not succeed
    chain.wait.for_block(sale.call().endBlock())
    with pytest.raises(TransactionFailed):
        send_eth_to_sale(chain, sale, customer, to_wei(1, 'ether'))

    # extend sale for 2 more blocks and re-try
    sale.transact().extendSale(2)
    send_eth_to_sale(chain, sale, customer, to_wei(1, 'ether'))
    assert token.call().balanceOf(customer) > 0
    assert chain.web3.eth.getBalance(sale.address) == to_wei(1, 'ether')
