import pytest

from eth_utils import to_wei, is_same_address
from web3.contract import Contract
from populus.chain.base import BaseChain
from ethereum.tester import TransactionFailed

from helpers import deploy_contract

contract_name = 'ViewlyTokenMintage'

class Bucket:
    Founders   = 0
    Supporters = 1
    Creators   = 2
    Bounties   = 3

def assert_last_payment_log(contract: Contract, recipient, tokens):
    event = contract.pastEvents('LogPayment').get()[-1]['args']
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

    category = lambda bucket: instance.call().categories(bucket)
    million = 1_000_000
    assert category(Bucket.Founders)[0] == to_wei(18 * million, 'ether')
    assert category(Bucket.Supporters)[0] == to_wei(9 * million, 'ether')
    assert category(Bucket.Creators)[0] == to_wei(20 * million, 'ether')
    assert category(Bucket.Bounties)[0] == to_wei(3 * million, 'ether')

def test_mint(chain, instance, token, recipient, recipient2):
    category = lambda bucket: instance.call().categories(bucket)

    instance.transact().mint(recipient, to_wei(1, 'ether'), Bucket.Founders)
    assert_last_payment_log(instance, recipient, to_wei(1, 'ether'))
    assert token.call().balanceOf(recipient) == to_wei(1, 'ether')
    assert category(Bucket.Founders)[1] == to_wei(1, 'ether')

    instance.transact().mint(recipient, to_wei(9, 'ether'), Bucket.Founders)
    assert_last_payment_log(instance, recipient, to_wei(9, 'ether'))
    assert token.call().balanceOf(recipient) == to_wei(10, 'ether')
    assert category(Bucket.Founders)[1] == to_wei(10, 'ether')

    instance.transact().mint(recipient2, to_wei(90, 'ether'), Bucket.Supporters)
    assert_last_payment_log(instance, recipient2, to_wei(90, 'ether'))
    assert token.call().balanceOf(recipient2) == to_wei(90, 'ether')
    assert category(Bucket.Founders)[1] == to_wei(10, 'ether')
    assert category(Bucket.Supporters)[1] == to_wei(90, 'ether')


def test_mint_fails_after_cap_reached(chain, instance, token, recipient):
    category = lambda bucket: instance.call().categories(bucket)

    founders_mint_max = category(Bucket.Founders)[0]
    instance.transact().mint(recipient, founders_mint_max, Bucket.Founders)
    assert category(Bucket.Founders)[1] == founders_mint_max

    # rewards cannot be distributed any more after cap is reached
    with pytest.raises(TransactionFailed):
        instance.transact().mint(recipient, 1, Bucket.Founders)

def test_mint_fails_when_bucket_invalid(chain, instance, token, recipient):
    invalid_bucket = 4  # Bucket enum is 0-4 only
    with pytest.raises(TransactionFailed):
        instance.transact().mint(recipient, 1, invalid_bucket)

def test_mint_fails_when_not_authorized(chain, instance, token, recipient):
    # sendTokenReward cannot be called by a random user
    with pytest.raises(TransactionFailed):
        instance.transact(
            {"from": recipient}).mint(recipient, 1, Bucket.Founders)
