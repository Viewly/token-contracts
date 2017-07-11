// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.11;

import "./lib/math.sol";
import "./lib/token.sol";
import "./lib/note.sol";
import "./lib/auth.sol";


contract ViewlySale is DSAuth, DSMath, DSNote {

    // this is useful for automated testing only
    // live contract SHOULD have this value set to false
    bool isTestable = false;

    // Where should secureETH() proxy the ETH raised?
    // Where should mintReserve() send the bounty/team vesting tokens?
    //
    // This address should be the DSMultisig80 contract address.
    // Ideally, withdrawals from this address require a quorum agreement from
    // the core team, legal and/or 3rd party escrows.
    //
    // Note: multisigAddr MUST implement a mechanism to transfer ERC-20 tokens,
    // otherwise all VIEW tokens sent to it will be permanently lost.
    address public constant multisigAddr = 0x0;  // todo set this

    // supply and allocation
    DSToken public VIEW;
    uint128 public constant tokenCreationCap = 100000000; // 100_000_000
    uint128 public constant mintMonthlyMax   = 2;         // 2% a month max

    // variables for current round set on round start
    uint8   public roundNumber;         // round 1,2,3...
    uint128 public roundEthCap;         // ETH cap for this round
    uint128 public roundTokenCap;       // Token cap for this round
    uint    public roundDurationHours;  // eg. 72 = 3 days
    uint256 public roundStartBlock;     // startSale() block
    uint256 public roundEndBlock;       // roundStartTime + N days

    // outstanding token claims
    // mapEthDeposits[roundNumber][address] = sum(msg.value)
    mapping (uint8 => mapping (address => uint)) public mapEthDeposits;

    // sums of Ether raised per round
    mapping (uint8 => uint) public mapEthSums;

    // total supply of tokens issued every round
    mapping (uint8 => uint) public mapTokenSums;

    // registration addresses
    mapping (address => string) public mapViewlyKeys;

    // state machine
    enum State {
        Pending,
        Running,
        Done
    }
    State public state = State.Pending;

    // minting history
    struct Mintage {
        uint amount;
        uint timestamp;
    }
    Mintage[] mintHistory;


    event LogBuy(
        uint8 roundNumber,
        address buyer,
        uint256 ethSent
    );

    event LogStartSale(
        uint8   roundNumber,
        uint256 roundStartBlock,
        uint256 roundEndBlock,
        uint128 roundTokenCap,
        uint128 roundEthCap
    );

    event LogEndSale(
        uint8 roundNumber,
        uint256 totalSupply
    );

    event LogRegister(
        address user,
        string key
    );

    event LogFreeze(
        uint256 blockNum
    );


    function ViewlySale(bool isTestable_) {
        // initialize the ERC-20 Token
        // is this a bad practice?
        // should the VIEW token be deployed by the
        // maintainer, and passed as address here?
        VIEW = new DSToken("VIEW");
        assert(VIEW.totalSupply() == 0);
        assert(VIEW.owner() == address(this));
        assert(VIEW.authority() == DSAuthority(0));

        if (isTestable_ == true) {
            isTestable = true;
        }
    }

    // fallback function
    // todo - gas issue: see http://bit.ly/2tMqjhf
    function () payable {
        buyTokens();
    }

    modifier isRunning() {
        if (state != State.Running) throw;
        _;
    }

    modifier notRunning() {
        if (state == State.Running) throw;
        _;
    }



    //
    // SALE
    // ----

    function startSale(
        uint roundDurationHours_,
        uint256 blockFutureOffset,
        uint128 roundTokenCap_,
        uint128 roundEthCap_
    )
        notRunning
        auth
        note
    {
        // this MUST be to_wei(x, 'ether')
        roundEthCap = roundEthCap_;

        roundTokenCap = roundTokenCap_;
        roundDurationHours = roundDurationHours_;

        // don't exceed the hard cap
        assert(add(totalSupply(), roundTokenCap) < tokenCreationCap);

        // We want to be able to start the sale contract for a block slightly
        // in the future, so that the start time is accurately known
        roundStartBlock = add(block.number, blockFutureOffset);

        // calculate roundEndBlock
        uint blocksPerHour = mul(div(60, 17), 60);
        uint blockNumDuration = mul(blocksPerHour, roundDurationHours);
        roundEndBlock = add(roundStartBlock, blockNumDuration);

        // start a new round
        roundNumber += 1;

        // allocate tokens from this round upfront
        mapTokenSums[roundNumber] = roundTokenCap;

        // enable the sale
        state = State.Running;

        LogStartSale(
            roundNumber,
            roundStartBlock,
            roundEndBlock,
            roundTokenCap,
            roundEthCap
        );

    }

    // anyone can end the sale
    function finalizeSale()
        isRunning
        note
    {
        assert(block.number > roundEndBlock);

        // State.Done
        state = State.Done;

        LogEndSale(
            roundNumber,
            mapEthSums[roundNumber]
        );
    }

    function buyTokens() isRunning payable {
        assert(block.number >= roundStartBlock);
        assert(block.number < roundEndBlock);
        if (msg.value == 0) throw;

        // check if ETH cap is reached for this sale
        assert(add(mapEthSums[roundNumber], msg.value) < roundEthCap);

        // issue the claim for the tokens
        mapEthDeposits[roundNumber][msg.sender] += msg.value;
        mapEthSums[roundNumber] += msg.value;

        LogBuy(roundNumber, msg.sender, msg.value);
    }



    //
    // HELPERS
    // -------

    // tokens issued from reserves + tokens issued in sale rounds
    function totalSupply() returns(uint256) {
        uint sum = 0;
        for (uint8 x = 0; x <= roundNumber; x++) {
            sum += mapTokenSums[x];
        }
        return add(mintedTotalSum(), sum);
    }

    function erc20Supply() constant returns(uint) {
        return VIEW.totalSupply();
    }

    // all ETH raised trough rounds
    function totalEth() returns(uint256) {
        uint sum = 0;
        for (uint8 x = 0; x <= roundNumber; x++) {
            sum += mapEthSums[x];
        }
        return sum;
    }

    function balanceOf(address address_) constant returns(uint256) {
        return VIEW.balanceOf(address_);
    }

    function unclaimedBalanceOf(uint8 roundNumber_, address address_)
        constant
        returns(uint256)
    {
        return mapEthDeposits[roundNumber_][address_];
    }


    //
    // CLAIM
    // -----

    // once the sale is ended, users can claim their share of tokens
    function claim(uint8 roundNumber_) notRunning {
        assert(roundNumber_ <= roundNumber);

        // see how much ETH was deposited by the user for this round
        uint etherSent = mapEthDeposits[roundNumber_][msg.sender];

        // calculate the amount of tokens to claim
        uint pctShare = div(etherSent, mapEthSums[roundNumber_]);
        uint128 tokens = cast(mul(pctShare, mapTokenSums[roundNumber_]));

        // make the transfer
        mapEthDeposits[roundNumber_][msg.sender] = 0;
        VIEW.push(msg.sender, tokens);
    }


    function registerViewlyAddr(string pubKey) {
        assert(bytes(pubKey).length <= 64);
        mapViewlyKeys[msg.sender] = pubKey;
        LogRegister(msg.sender, pubKey);
    }

    // freeze the token before the snapshot
    function freeze() auth {
        VIEW.stop();
        LogFreeze(block.number);
    }

    // forward the funds from the contract to a mulitsig addr.
    function secureEth() auth note returns(bool) {
        assert(this.balance > 0);
        return multisigAddr.send(this.balance);
    }


    //
    // RESERVED TOKENS
    // ---------------

    // An arbitrary amount of reserve tokens can be minted,
    // but no more than 2% of total supply per month.
    // Minting is disabled during the token sale.
    function mintReserve(uint requestedAmount)
        notRunning
        auth
        returns(uint toMint)
    {
        toMint = requestedAmount;

        // calculate remaining monthly allowance
        uint monthlyAllowance = sub(mintableTokenAmount(), mintedLastMonthSum());
        assert(monthlyAllowance > 0);

        // soft cap to the available monthly allowance
        if (toMint > monthlyAllowance) {
            toMint = monthlyAllowance;
        }

        // don't forget about the hard cap
        uint availableSupply = sub(tokenCreationCap, totalSupply());
        if (toMint > availableSupply) {
            toMint = availableSupply;
        }

        // mint the new tokens
        VIEW.mintTo(multisigAddr, cast(toMint));

        // log mintage
        mintHistory.push(Mintage(toMint, block.timestamp));
    }

    // sum(x.amount for x in mintHistory if x.timestamp > last_30_days)
    function mintedLastMonthSum() constant returns(uint sumMinted) {
        uint monthAgo = block.timestamp - 30 days;

        sumMinted = 0;
        for(uint8 x = 0; x < mintHistory.length; x++)
        {
            if (mintHistory[x].timestamp > monthAgo) {
                sumMinted += mintHistory[x].amount;
            }
        }
    }

    // sum(x.amount for x in mintHistory if x.timestamp > last_30_days)
    function mintedTotalSum() constant returns(uint sumMinted) {
        sumMinted = 0;
        for(uint8 x = 0; x < mintHistory.length; x++)
        {
            sumMinted += mintHistory[x].amount;
        }
    }

    // 2% of total supply = ?
    function mintableTokenAmount() constant returns(uint) {
        uint multiplier = mul(tokenCreationCap, mintMonthlyMax);
        return div(multiplier, 100);
    }


    //
    // TEST HELPERS
    // ------------
    //
    // These methods are to be used in the contract test suite
    // and will not be accessible in the real sale contract.

    modifier mustBeTestable() {
        if (isTestable != true) throw;
        _;
    }

    // use this method to satisfy finalizeSale block requirement
    function collapseBlockTimes()
        mustBeTestable
        isRunning
        auth
    {
        roundEndBlock = add(roundStartBlock, 1);
    }

}
