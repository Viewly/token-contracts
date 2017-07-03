// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.11;

//import "./math.sol";
//import "./token.sol";
//import "./note.sol";
//import "./auth.sol";

import "ds-math/math.sol";
import "ds-token/token.sol";
import "ds-note/note.sol";
import "ds-auth/auth.sol";


contract ViewlySaleRecurrent is DSAuth, DSMath, DSNote {

    // account where the crowdsale funds will be proxied to - see secureETH()
    address public constant multisigAddr = 0x0;  // todo set this

    // supply and allocation
    DSToken public VIEW;
    uint128 public constant tokenCreationCap = 100000000; // 100_000_000
    uint128 public          mintMonthlyMax   = 2;         // 2% a month max

    // variables calculated on round start
    uint128 public roundUsdCap;         // USD cap for this round
    uint128 public roundTokenCap;       // based on roundUsdCap
    uint128 public roundTokenSupply;    // reset to 0 with every round
    uint128 public roundExchangeRate;   // eg. 1000 VIEW for 1 ETH
    uint    public roundDurationHours;  // eg. 72 = 3 days
    uint256 public roundStartBlock;     // startSale() block
    uint256 public roundEndBlock;       // roundStartTime + N days

    // claim addresses
    mapping (address => string) public viewlyKeys;

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
        address user,
        uint256 ethSent,
        uint256 tokenAmount,
        uint256 roundTokenSupply
    );

    event LogStartSale(
        uint256 roundStartBlock,
        uint256 roundEndBlock,
        uint128 roundTokenSupply,
        uint128 roundExchangeRate,
        uint128 ethUsdPrice
    );

    event LogEndSale(
        uint256 totalSupply
    );

    event LogRegister(
        address user,
        string key
    );

    event LogFreeze(uint256 blockNum);



    function ViewlySaleRecurrent() {
        // initialize the ERC-20 Token
        VIEW = new DSToken("VIEW");
        assert(VIEW.totalSupply() == 0);
        assert(VIEW.owner() == address(this));
        assert(VIEW.authority() == DSAuthority(0));
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



//    // todo: remove this before deploying contract for real
//    function startSaleStub() notRunning auth {
//        // 1hr, 0 offset, $300 ETH
//        startSale(1, 0, 300);
//    }
//
//    // todo: remove this before deploying contract for real
//    function endSaleStub() isRunning auth {
//        roundEndBlock = add(roundStartBlock, 1);
//        finalizeSale();
//    }

    function startSale(
        uint roundDurationHours_,
        uint256 blockFutureOffset,
        uint128 roundTokenCap_,
        uint128 roundUsdCap_,
        uint128 ethUsdPrice
    )
        notRunning
        auth
        note
    {
        roundTokenCap = roundTokenCap_;
        roundUsdCap = roundUsdCap_;
        roundDurationHours = roundDurationHours_;

        // don't exceed the hard cap
        assert(add(totalSupply(), roundTokenCap) < tokenCreationCap);

        // calculate roundExchangeRate
        roundExchangeRate = wmul(wdiv(roundTokenCap, roundUsdCap), ethUsdPrice);

        // We want to be able to start the sale contract for a block slightly
        // in the future, so that the start time is accurately known
        roundStartBlock = add(block.number, blockFutureOffset);

        // calculate roundEndBlock
        uint blocksPerHour = mul(div(60, 17), 60);
        uint blockNumDuration = mul(blocksPerHour, roundDurationHours);
        roundEndBlock = add(roundStartBlock, blockNumDuration);

        state = State.Running;

        LogStartSale(
            roundStartBlock,
            roundEndBlock,
            roundTokenCap,
            roundExchangeRate,
            ethUsdPrice
        );

    }

    function finalizeSale()
        isRunning
        auth
        note
    {
        assert(block.number > roundEndBlock);

        // State.Done
        state = State.Done;

        // reset
        roundTokenSupply = 0;
        roundTokenCap = 0;
        roundUsdCap = 0;

        LogEndSale(
            totalSupply()
        );
    }

    function buyTokens() isRunning payable {
        assert(block.number >= roundStartBlock);
        assert(block.number < roundEndBlock);
        if (msg.value == 0) throw;

        // calculate the tokens to be allocated
        uint256 tokens = mul(msg.value, roundExchangeRate);

        // check if the sale is over the cap
        uint256 postSaleSupply = add(roundTokenSupply, tokens);
        if (postSaleSupply > roundTokenCap) throw;

        // award the tokens
        VIEW.mint(cast(tokens));

        // tally up the total round issued supply
        roundTokenSupply = cast(postSaleSupply);

        LogBuy(msg.sender, msg.value, tokens, roundTokenSupply);
    }



    //
    // HELPERS
    // -------
    function totalSupply() returns(uint256) {
        return VIEW.totalSupply();
    }

    function balanceOf(address address_) constant returns(uint256) {
        return VIEW.balanceOf(address_);
    }



    //
    // CLAIM
    // -----
    function registerViewlyAddr(string pubKey) {
        assert(bytes(pubKey).length <= 64);
        viewlyKeys[msg.sender] = pubKey;
        LogRegister(msg.sender, pubKey);
    }

    // freeze the token before the snapshot
    function freeze() auth {
        VIEW.stop();
        LogFreeze(block.number);
    }

    // forward the funds from the contract to a mulitsig addr.
    function secureETH() auth note returns(bool) {
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

        // calculate remaining monthly allowance
        uint monthlyAllowance = sub(mintMonthlyTokens(), mintedLastMonthSum());
        assert(monthlyAllowance > 0);

        // soft cap to the available monthly allowance
        toMint = 0;
        if (requestedAmount > monthlyAllowance) {
            toMint = monthlyAllowance;
        }

        // don't forget about the hard cap
        uint availableSupply = sub(tokenCreationCap, totalSupply());
        if (toMint > availableSupply) {
            toMint = availableSupply;
        }

        // mint the new tokens
        VIEW.mint(cast(toMint));

        // transfer minted tokens to a multisig wallet
        uint balance = VIEW.balanceOf(msg.sender);
        if (!VIEW.transfer(multisigAddr, balance)) throw;
    }

    // sum(x.amount for x in mintHistory if x.timestamp > last_30_days)
    function mintedLastMonthSum() constant returns(uint sumMinted) {
        uint monthAgo = block.timestamp - 30 days;

        sumMinted = 0;
        for(uint8 x = 0; x < mintHistory.length; x++)
        {
            if (mintHistory[x].timestamp < monthAgo) {
                sumMinted += mintHistory[x].amount;
            }
        }
    }

    // 2% of total supply = ?
    function mintMonthlyTokens() constant returns(uint) {
        return cast(wdiv(wmul(tokenCreationCap, mintMonthlyMax), 100));
    }


}
