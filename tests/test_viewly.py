def test_init(chain):
    greeter, _ = chain.provider.get_or_deploy_contract('ViewlyAuctionRecurrent')

    # sanity check, values should be initalized to 0
    assert greeter.call().roundNumber() == 0
