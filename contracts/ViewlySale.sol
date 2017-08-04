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
    address public multisigAddr;  // todo set this

    // supply and allocation
    DSToken public VIEW;
    uint128 public constant tokenCreationCap = 100000000 ether;
    uint128 public constant mintMonthlyMax   = 2;                  // 2% a month max

    // variables for current sale round on startSaleRound
    uint8   public roundNumber;         // round 1,2,3...
    uint128 public roundEthCap;         // ETH cap in WEI
    uint128 public roundTokenCap;       // Token cap in WEI
    uint    public roundDurationBlocks; // 72 * 3600 // 17 = 15247 blocks
                                        // =~ 3 days
    uint    public roundStartBlock;     // sale round start block
    uint    public roundEndBlock;       // sale round end block

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
        uint ethSent
    );

    event LogClaimTokens(
        uint8 roundNumber,
        address buyer,
        uint ethBurned,
        uint128 tokensSent
    );

    event LogStartSaleRound(
        uint8 roundNumber,
        uint roundStartBlock,
        uint roundEndBlock,
        uint128 roundTokenCap,
        uint128 roundEthCap
    );

    event LogEndSaleRound(
        uint8 roundNumber,
        uint totalSupply
    );

    event LogRegister(
        address user,
        string key
    );

    event LogFreeze(
        uint blockNum
    );


    function ViewlySale(address multisigAddr_, bool isTestable_) {
        multisigAddr = multisigAddr_;

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
        require(state == State.Running);
        _;
    }

    modifier notRunning() {
        require(state != State.Running);
        _;
    }



    //
    // SALE
    // ----

    function startSaleRound(
        uint roundDurationBlocks_,
        uint blockFutureOffset,
        uint128 roundTokenCap_,
        uint128 roundEthCap_
    )
        notRunning
        auth
        note
    {
        // sanity checks
        require(roundDurationBlocks_ > 0);
        require(roundTokenCap_ > 0);
        require(roundEthCap_ > 0);

        roundEthCap = roundEthCap_;
        roundTokenCap = roundTokenCap_;
        roundDurationBlocks = roundDurationBlocks_;

        // don't exceed the hard cap
        require(add(totalSupply(), roundTokenCap) <= tokenCreationCap);

        // We want to be able to start the sale round for a block slightly
        // in the future, so that the start time is accurately known
        roundStartBlock = add(block.number, blockFutureOffset);
        roundEndBlock = add(roundStartBlock, roundDurationBlocks);

        // start a new round
        roundNumber += 1;

        // allocate tokens from this round upfront
        mapTokenSums[roundNumber] = roundTokenCap;

        // enable the sale
        state = State.Running;

        LogStartSaleRound(
            roundNumber,
            roundStartBlock,
            roundEndBlock,
            roundTokenCap,
            roundEthCap
        );

    }

    // anyone can end the sale round
    function endSaleRound()
        isRunning
        note
    {
        require(block.number > roundEndBlock);

        // State.Done
        state = State.Done;

        LogEndSaleRound(
            roundNumber,
            mapEthSums[roundNumber]
        );
    }

    function buyTokens() isRunning payable {
        require(block.number >= roundStartBlock);
        require(block.number < roundEndBlock);
        require(msg.value > 0);

        // check ETH cap not reached for this sale round
        require(add(mapEthSums[roundNumber], msg.value) <= roundEthCap);

        // issue the claim for the tokens
        mapEthDeposits[roundNumber][msg.sender] += msg.value;
        mapEthSums[roundNumber] += msg.value;

        LogBuy(roundNumber, msg.sender, msg.value);
    }



    //
    // HELPERS
    // -------

    // tokens issued from reserves + tokens issued in sale rounds
    function totalSupply() returns(uint) {
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
    function totalEth() returns(uint) {
        uint sum = 0;
        for (uint8 x = 0; x <= roundNumber; x++) {
            sum += mapEthSums[x];
        }
        return sum;
    }

    function balanceOf(address address_) constant returns(uint) {
        return VIEW.balanceOf(address_);
    }


    //
    // CLAIM
    // -----

    // once the sale round is ended, users can claim their share of tokens
    function claim(uint8 roundNumber_) notRunning returns(uint128){
        // the round must had happened
        require(roundNumber_ > 0);
        require(roundNumber_ <= roundNumber);

        // there should be funds in the round
        require(mapEthSums[roundNumber_] > 0);

        // see how much ETH was deposited by the user for this round
        uint etherSent = mapEthDeposits[roundNumber_][msg.sender];
        require(etherSent > 0);

        // calculate the amount of tokens to claim
        uint128 price = wdiv(cast(mapTokenSums[roundNumber_]), cast(mapEthSums[roundNumber_]));
        uint128 tokens = wmul(cast(etherSent), price);
        assert(tokens > 0);

        // burn the deposit
        mapEthDeposits[roundNumber_][msg.sender] = 0;

        // mint the new tokens
        VIEW.mintTo(msg.sender, tokens);

        LogClaimTokens(
            roundNumber_,
            msg.sender,
            etherSent,
            tokens
        );
        return tokens;
    }

    // # This code somehow works, but I have no idea how. Should ask for expert advice.
    // uint128 price = wdiv(cast(mapTokenSums[roundNumber_]), cast(mapEthSums[roundNumber_]));
    //
    // # Why does this not work? Its *almost* the same code!
    // uint price = div(mapTokenSums[roundNumber_], mapEthSums[roundNumber_]);


    // takes a hex encoded public key
    function registerViewlyAddr(string pubKey) {
        // (length == 54) -> VIEW7ab...xYz ?
        require(bytes(pubKey).length <= 64);
        mapViewlyKeys[msg.sender] = pubKey;
        LogRegister(msg.sender, pubKey);
    }

    // Note: Freezing the token may cause issues with exchange held funds.
    // It might be better to leave the transfers open indefinitely,
    // and offer a burn contract + converter service,
    // so that users can freely withdraw their tokens
    // from centralized exchanges and convert them.
    function freeze() auth {
        VIEW.stop();
        LogFreeze(block.number);
    }

    // forward the funds from the contract to a mulitsig addr.
    function secureEth() auth note returns(bool) {
        require(this.balance > 0);
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
        require(monthlyAllowance > 0);

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
        require(isTestable);
        _;
    }

    // use this method to satisfy endSaleRound block requirement
    function collapseBlockTimes()
        mustBeTestable
        isRunning
        auth
    {
        roundEndBlock = add(roundStartBlock, 1);
    }

}
