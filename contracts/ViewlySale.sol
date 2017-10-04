// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.11;

import "./dappsys/math.sol";
import "./dappsys/token.sol";
import "./dappsys/note.sol";
import "./dappsys/auth.sol";


contract ViewlySale is DSAuth, DSMath, DSNote {

    // Address where secureETH() and mintReserve send tokens or ethers.
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
    // absolute hard cap of token supply (1 Billion)
    uint public constant tokenCreationCap = 1000000000 ether;
    // 2% per month mintable token cap
    uint public constant mintMonthlyCap = wmul(tokenCreationCap, 0.02 ether);

    // variables for current sale round on startSaleRound
    uint8   public roundNumber;         // round 1,2,3...
    uint    public roundEthCap;         // ETH cap in WEI
    uint    public roundTokenCap;       // Token cap in WEI
    uint    public roundDurationBlocks; // 72 * 3600 // 17 =~ 3 days
    uint    public roundStartBlock;     // sale round start block
    uint    public roundEndBlock;       // sale round end block

    // ether sent in round, by contributor
    mapping (uint8 => mapping (address => uint)) public ethDeposits;

    // sums of ether raised per round
    mapping (uint8 => uint) public ethRaisedInRound;

    // total supply of tokens issued in round
    mapping (uint8 => uint) public tokenSupplyInRound;

    // registration addresses
    mapping (address => string) public viewlyKeys;

    enum State {
        Pending,
        Running,
        Done
    }
    State public state = State.Pending;

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
        uint tokensSent
    );

    event LogStartSaleRound(
        uint8 roundNumber,
        uint roundStartBlock,
        uint roundEndBlock,
        uint roundTokenCap,
        uint roundEthCap
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


    modifier isRunning() {
        require(state == State.Running);
        _;
    }

    modifier notRunning() {
        require(state != State.Running);
        _;
    }


    function ViewlySale(DSToken view_, address multisigAddr_) {
        VIEW = view_;
        multisigAddr = multisigAddr_;
    }

    //
    // SALE
    // ----

    function startSaleRound(
        uint roundDurationBlocks_,
        uint blockFutureOffset,
        uint roundTokenCap_,
        uint roundEthCap_
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
        require(add(totalTokenSupply(), roundTokenCap) <= tokenCreationCap);

        // We want to be able to start the sale round for a block slightly
        // in the future, so that the start time is accurately known
        roundStartBlock = add(block.number, blockFutureOffset);
        roundEndBlock = add(roundStartBlock, roundDurationBlocks);

        // start a new round
        roundNumber += 1;

        // allocate tokens from this round upfront
        tokenSupplyInRound[roundNumber] = roundTokenCap;

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

        state = State.Done;

        LogEndSaleRound(
            roundNumber,
            ethRaisedInRound[roundNumber]
        );
    }

    function buyTokens() isRunning payable {
        require(block.number >= roundStartBlock);
        require(block.number < roundEndBlock);
        require(msg.value > 0);

        // check ETH cap not reached for this sale round
        require(add(ethRaisedInRound[roundNumber], msg.value) <= roundEthCap);

        // issue the claim for the tokens
        ethDeposits[roundNumber][msg.sender] += msg.value;
        ethRaisedInRound[roundNumber] += msg.value;

        LogBuy(roundNumber, msg.sender, msg.value);
    }

    function () payable {
        buyTokens();
    }


    //
    // CLAIM
    // -----

    // once the sale round is ended users can claim their share of tokens
    function claim(uint8 roundNumber_) notRunning returns(uint){
        // the round must had happened
        require(roundNumber_ > 0);
        require(roundNumber_ <= roundNumber);

        // there should be funds in this round
        require(ethRaisedInRound[roundNumber_] > 0);

        // claimant should have sent ether in this round
        uint etherSent = ethDeposits[roundNumber_][msg.sender];
        require(etherSent > 0);

        uint tokens = calculateTokensRewardFor(etherSent, roundNumber_);
        assert(tokens > 0);

        // burn the deposit
        ethDeposits[roundNumber_][msg.sender] = 0;

        // mint the new tokens
        VIEW.mint(msg.sender, tokens);

        LogClaimTokens(roundNumber_, msg.sender, etherSent, tokens);

        return tokens;
    }

    // takes a hex encoded public key
    function registerViewlyAddress(string pubKey) {
        // (length == 54) -> VIEW7ab...xYz ?
        require(bytes(pubKey).length <= 64);
        viewlyKeys[msg.sender] = pubKey;
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
        uint monthlyAllowance = sub(mintMonthlyCap, mintedLastMonth());
        require(monthlyAllowance > 0);

        // soft cap to the available monthly allowance
        if (toMint > monthlyAllowance) {
            toMint = monthlyAllowance;
        }

        // don't forget about the hard cap
        uint availableSupply = sub(tokenCreationCap, totalTokenSupply());
        if (toMint > availableSupply) {
            toMint = availableSupply;
        }

        // mint the new tokens
        VIEW.mint(multisigAddr, toMint);

        // log mintage
        mintHistory.push(Mintage(toMint, block.timestamp));
    }


    //
    // HELPERS
    // -------

    // tokens issued from reserves + tokens issued in sale rounds
    function totalTokenSupply() constant returns(uint supply) {
        supply = 0;
        for (uint8 x = 0; x <= roundNumber; x++) {
            supply += tokenSupplyInRound[x];
        }
        supply += totalMinted();
    }

    // all ETH raised trough rounds
    function totalEthRaised() constant returns(uint eth) {
        eth = 0;
        for (uint8 x = 0; x <= roundNumber; x++) {
            eth += ethRaisedInRound[x];
        }
    }

    function balanceOf(address address_) constant returns(uint) {
        return VIEW.balanceOf(address_);
    }

    function mintedLastMonth() constant returns(uint minted) {
        uint monthAgo = block.timestamp - 30 days;

        minted = 0;
        for(uint8 x = 0; x < mintHistory.length; x++) {
            if (mintHistory[x].timestamp > monthAgo) {
                minted += mintHistory[x].amount;
            }
        }
    }

    function totalMinted() constant returns(uint minted) {
        minted = 0;
        for(uint8 x = 0; x < mintHistory.length; x++) {
            minted += mintHistory[x].amount;
        }
    }

    // calculate tokens reward for ether sent in given sale round
    function calculateTokensRewardFor(uint etherSent, uint8 roundNumber)
        private constant returns(uint tokensReward)
    {
        uint totalEtherInRound = ethRaisedInRound[roundNumber];
        uint totalTokensInRound = tokenSupplyInRound[roundNumber];
        uint tokensShare = wdiv(etherSent, totalEtherInRound);
        tokensReward = wmul(tokensShare, totalTokensInRound);
    }
}
