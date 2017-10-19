import pytest

from eth_utils import to_wei
from web3.contract import Contract
from populus.chain.base import BaseChain
from ethereum.tester import TransactionFailed


MAX_TOKEN_REWARDS = to_wei(3_000_000, 'ether')

def deploy_contract(chain: BaseChain, contract_name: str, args=[]) -> Contract:
    # deploy contract on chain with coinbase and optional init args
    factory = chain.get_contract_factory(contract_name)
    deploy_tx_hash = factory.deploy(args=args)
    contract_address = chain.wait.for_contract_address(deploy_tx_hash)
    return factory(address=contract_address)

def assert_last_token_reward_event(bounty, recipient, tokens):
    event = bounty.pastEvents('LogTokenReward').get()[-1]['args']
    assert event['recipient'] == recipient
    assert event['tokens'] == tokens


@pytest.fixture()
def token(chain: BaseChain) -> Contract:
    """ A VIEW token contract. """
    return deploy_contract(chain, 'DSToken', args=['VIEW'])

@pytest.fixture()
def bounty(chain: BaseChain, token: Contract) -> Contract:
    """ A ViewlyBountyRewards contract. """
    bounty = deploy_contract(chain, 'ViewlyBountyRewards', args=[token.address])
    token.transact().setOwner(bounty.address)
    return bounty

@pytest.fixture
def owner(accounts) -> str:
    return accounts[0]

@pytest.fixture
def recipient(accounts) -> str:
    return accounts[1]

@pytest.fixture
def recipient2(accounts) -> str:
    return accounts[2]


def test_init(chain, bounty, token):
    assert bounty.call().viewToken() == token.address
    assert bounty.call().totalTokenRewards() == 0

def test_send_token_reward(chain, bounty, token, recipient, recipient2):
    bounty.transact().sendTokenReward(recipient, to_wei(1, 'ether'))
    assert token.call().balanceOf(recipient) == to_wei(1, 'ether')
    assert_last_token_reward_event(bounty, recipient, to_wei(1, 'ether'))

    bounty.transact().sendTokenReward(recipient, to_wei(9, 'ether'))
    assert token.call().balanceOf(recipient) == to_wei(10, 'ether')
    assert bounty.call().tokenRewards(recipient) == to_wei(10, 'ether')
    assert_last_token_reward_event(bounty, recipient, to_wei(9, 'ether'))

    bounty.transact().sendTokenReward(recipient2, to_wei(90, 'ether'))
    assert token.call().balanceOf(recipient2) == to_wei(90, 'ether')
    assert bounty.call().tokenRewards(recipient2) == to_wei(90, 'ether')
    assert_last_token_reward_event(bounty, recipient2, to_wei(90, 'ether'))

    assert bounty.call().totalTokenRewards() == to_wei(100, 'ether')

def test_send_token_reward_fails_after_cap_reached(chain, bounty, token, recipient):
    bounty.transact().sendTokenReward(recipient, MAX_TOKEN_REWARDS)
    assert token.call().balanceOf(recipient) == MAX_TOKEN_REWARDS

    # rewards cannot be distributed any more after cap is reached
    with pytest.raises(TransactionFailed):
        bounty.transact().sendTokenReward(recipient, 1)

def test_send_token_reward_fails_when_not_authorized(chain, bounty, token, recipient):
    # sendTokenReward cannot be called by a random user
    with pytest.raises(TransactionFailed):
        bounty.transact({"from": recipient}).sendTokenReward(recipient, 1)
