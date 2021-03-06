import pytest

from eth_utils import to_wei, is_same_address
from web3.contract import Contract
from populus.chain.base import BaseChain
from ethereum.tester import TransactionFailed

from helpers import deploy_contract

contract_name = 'ViewTokenMintage'

class CategoryId:
    Team       = 0
    Supporters = 1
    Creators   = 2
    Bounties   = 3
    SeedSale   = 4
    MainSale   = 5

def assert_last_tokens_minted(contract: Contract, recipient, tokens):
    event = contract.pastEvents('TokensMinted').get()[-1]['args']
    assert event['recipient'] == recipient
    assert event['tokens'] == tokens


@pytest.fixture()
def token(chain: BaseChain) -> Contract:
    """ The VIEW ERC-20 Token contract. """
    return deploy_contract(chain, 'DSToken', args=['VIEW'])

@pytest.fixture()
def instance(chain: BaseChain, token: Contract) -> Contract:
    contract = deploy_contract(
        chain, contract_name, args=[token.address])
    token.transact().setOwner(contract.address)
    return contract

@pytest.fixture
def owner(accounts) -> str:
    return accounts[0]

@pytest.fixture
def recipient(accounts) -> str:
    return accounts[1]

@pytest.fixture
def recipient2(accounts) -> str:
    return accounts[2]


def test_init(chain, instance, token):
    assert is_same_address(instance.call().viewToken(), token.address)

    category = lambda category: instance.call().categories(category)
    million = 1_000_000
    assert category(CategoryId.Team)[0] == to_wei(18 * million, 'ether')
    assert category(CategoryId.Supporters)[0] == to_wei(9 * million, 'ether')
    assert category(CategoryId.Creators)[0] == to_wei(20 * million, 'ether')
    assert category(CategoryId.Bounties)[0] == to_wei(3 * million, 'ether')
    assert category(CategoryId.SeedSale)[0] == to_wei(10 * million, 'ether')
    assert category(CategoryId.SeedSale)[1] == to_wei(10 * million, 'ether')
    assert category(CategoryId.MainSale)[0] == to_wei(40 * million, 'ether')

def test_mint(chain, instance, token, recipient, recipient2):
    category = lambda category: instance.call().categories(category)

    instance.transact().mint(recipient, to_wei(1, 'ether'), CategoryId.Team)
    assert_last_tokens_minted(instance, recipient, to_wei(1, 'ether'))
    assert token.call().balanceOf(recipient) == to_wei(1, 'ether')
    assert category(CategoryId.Team)[1] == to_wei(1, 'ether')

    instance.transact().mint(recipient, to_wei(9, 'ether'), CategoryId.Team)
    assert_last_tokens_minted(instance, recipient, to_wei(9, 'ether'))
    assert token.call().balanceOf(recipient) == to_wei(10, 'ether')
    assert category(CategoryId.Team)[1] == to_wei(10, 'ether')

    instance.transact().mint(recipient2, to_wei(90, 'ether'), CategoryId.Supporters)
    assert_last_tokens_minted(instance, recipient2, to_wei(90, 'ether'))
    assert token.call().balanceOf(recipient2) == to_wei(90, 'ether')
    assert category(CategoryId.Team)[1] == to_wei(10, 'ether')
    assert category(CategoryId.Supporters)[1] == to_wei(90, 'ether')


def test_mint_fails_after_cap_reached(chain, instance, token, recipient):
    category = lambda category: instance.call().categories(category)

    team_mint_max = category(CategoryId.Team)[0]
    instance.transact().mint(recipient, team_mint_max, CategoryId.Team)
    assert category(CategoryId.Team)[1] == team_mint_max

    # rewards cannot be distributed any more after cap is reached
    with pytest.raises(TransactionFailed):
        instance.transact().mint(recipient, 1, CategoryId.Team)

def test_mint_fails_when_category_invalid(chain, instance, token, recipient):
    invalid_category = 6
    with pytest.raises(TransactionFailed):
        instance.transact().mint(recipient, 1, invalid_category)

def test_mint_fails_when_not_authorized(chain, instance, token, recipient):
    # sendTokenReward cannot be called by a random user
    with pytest.raises(TransactionFailed):
        instance.transact(
            {"from": recipient}).mint(recipient, 1, CategoryId.Team)

def test_destruct(chain, instance, token, owner):
    instance.transact().mint(owner, 1, CategoryId.Team)
    instance.transact().destruct(owner)

    # minting doesn't work after contract is destructed
    with pytest.raises(Exception):
        instance.transact().mint(recipient, 1, CategoryId.Team)

def test_total_mint_limit(chain, instance):
    assert instance.call().totalMintLimit() == to_wei(100_000_000, 'ether')
