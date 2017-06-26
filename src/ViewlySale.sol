// The MIT License (MIT)
// Copyright (c) 2017 Viewly (https://view.ly)

pragma solidity ^0.4.11;

//import "ds-math/math.sol";
//import "ds-token/token.sol";

import "ds-math/math.sol";
import "ds-note/note.sol";
import "ds-auth/auth.sol";

import  {DSToken} from "ds-token/token.sol";

contract ViewlySale is DSAuth, DSMath, DSNote {

    // account where the crowdsale funds will be proxied to
    address public constant multisigAddr = 0x0;  // todo set this

    // supply and allocation
    DSToken public VIEW;
    uint128 public constant tokenCreationCap = 100000000;   // 100_000_000
    uint128 public constant reservedAllocation = 0.2 ether; // 20%


    // crowsdale specs
    uint public constant saleDurationHours = 3 * 24;  // 3 days

    // variables calculated on sale start
    uint128 public constant usdSaleCap = 50000000;  // $50M
    uint128 public maxTokensForSale;
    uint128 public tokenExchangeRate;  // eg. 1000 VIEW for 1 ETH
    uint256 public fundingStartBlock;  // startSale() block
    uint256 public fundingEndBlock;    // fundingStartBlock + N days


    // state machine
    enum State {
        Pending,
        Running,
        Done
    }
    State public state = State.Pending;

    // future proofing
    struct Claim {
        bytes32 viewlyAddr;
        uint256 amount;
    }
    mapping (address => Claim) public viewlyClaims;
    mapping (bytes32 => address) public reverseViewlyClaims;

    // mapping (address => bytes32[]) public foo;

    // each viewly address can get coins from multiple ETH addresses,
    // or same address multiple times
    // bytes32 => []Claim
    // bytes32 => address => Claim  :: here we increment deposits in 1:1 relationships
    // each ETH address can reference multiple viewly addresses
    // address => []bytes32


    event Debug(uint256 msg);


    function ViewlySale() {
        // initialize the ERC-20 Token
        VIEW = new DSToken("VIEW");
        assert(VIEW.totalSupply() == 0);
        assert(VIEW.owner() == address(this));
        assert(VIEW.authority() == DSAuthority(0));
    }

//    function initialize(DSToken viewToken) auth note {
//        assert(state == State.Pending);
//
//        // initialize the ERC-20 Token
//        assert(viewToken.totalSupply() == 0);
////        assert(address(viewToken) == address(0));
//        assert(viewToken.owner() == address(this));
//        assert(viewToken.authority() == DSAuthority(0));
//        VIEW = viewToken;
//
//    }

    modifier isRunning() {
        if (state != State.Running) throw;
        _;
    }

    // fallback function
    // triggered when people send ETH directly to this contract
    function () payable {
        issueTokens();
    }


    function issueTokens() isRunning payable {
        assert(block.number >= fundingStartBlock);
        assert(block.number < fundingEndBlock);
        if (msg.value == 0) throw;

        // calculate the tokens to be allocated
        uint256 tokens = mul(msg.value, tokenExchangeRate);

        // check if the sale is over the cap
        uint256 currentSupply = add(VIEW.totalSupply(), calcReservedSupply());
        uint256 postSaleSupply = add(currentSupply, tokens);
        if (tokenCreationCap < postSaleSupply) throw;

        // award the tokens
        VIEW.mint(cast(tokens));

        Debug(tokens);
        Debug(VIEW.totalSupply());

    }

    function startSale(
        uint256 blockFutureOffset,
        uint128 ethUsdPrice
    )
        auth
        note
    {
        // the sale can be in Running state before its fundingStartBlock
        // We want to be able to start the sale contract for a block slightly
        // in the future, so that the start time is accurately known
        state = State.Running;
        fundingStartBlock = add(block.number, blockFutureOffset);

        // calculate fundingEndBlock
        uint blocksPerHour = mul(div(60, 17), 60);
        uint blockNumDuration = mul(blocksPerHour, saleDurationHours);
        fundingEndBlock = add(fundingStartBlock, blockNumDuration);

        // calculate tokenExchangeRate
        maxTokensForSale = wmul(wsub(1 ether, reservedAllocation), tokenCreationCap);
        tokenExchangeRate = wmul(wdiv(maxTokensForSale, usdSaleCap), ethUsdPrice);
        //
    }

    // create reservedAllocation, and transfer it to the multisig wallet
    // then close the sale state (State.Done)
    function finalizeSale()
        isRunning
        auth
        note
    {
        assert(block.number > fundingEndBlock);

        // mint reserved tokens
        uint256 reservedSupply = calcReservedSupply();
        VIEW.mint(cast(reservedSupply));

        // transfer reserved tokens to multisig wallet
        uint256 balance = VIEW.balanceOf(msg.sender);
        if (!VIEW.transfer(multisigAddr, balance)) throw;

        // State.Done
        nextState();
    }

    function calcReservedSupply() constant returns(uint256) {
        uint256 totalSupply = VIEW.totalSupply();
        uint256 supplyPct = sub(1, reservedAllocation);
        uint256 reservedSupply = mul(div(totalSupply, supplyPct), reservedAllocation);
        return reservedSupply;
    }

    function nextState() auth note returns(bool) {
        // we can only iterate trough states once
        if (state == State.Done) return false;
        state = State(uint(state) + 1);
        return true;
    }

    function balanceOf(address address_) constant returns(uint256) {
        return VIEW.balanceOf(address_);
    }

    function totalSupply() returns(uint256) {
        uint256 supply = VIEW.totalSupply();
        if (state == State.Running) {
            return add(supply, calcReservedSupply());
        }
        return supply;
    }

    // anyone can call this function to drain the contract
    // and forward funds into secure multisig wallet
    function secureETH() note returns(bool) {
        assert(this.balance > 0);
        return multisigAddr.send(this.balance);
    }

    // ---------------
    // CLAIM FUNCTIONS
    // ---------------

    // Allow token holders to register their Viewly public key.
    // This operation destroys VIEW tokens on Ethereum.
    // Addresses registered here will be included in Viewly genesis, or
    // be claimable at the registration faucet.
    function registerAndBurn(bytes32 viewlyChainAddr, uint256 amountToBurn) note {
        assert(state == State.Done);
        uint256 balance = VIEW.balanceOf(msg.sender);
        assert(balance > 0);
        assert(balance > amountToBurn);
        VIEW.burn(cast(balance));

        // if the user already claimed an amount, add to previous entry
        Claim existingClaim = viewlyClaims[msg.sender];
        if (existingClaim.amount > 0) {
            // don't allow the change of existing address to avoid possible double-issuance
            assert(existingClaim.viewlyAddr == viewlyChainAddr);

            // add to the old balance
            existingClaim.amount = add(existingClaim.amount, balance);
            viewlyClaims[msg.sender] = existingClaim;
        } else {
            viewlyClaims[msg.sender] = Claim(viewlyChainAddr, balance);
            reverseViewlyClaims[viewlyChainAddr] = msg.sender;
        }

    }

    function balanceOfViewlyAddr(bytes32 viewlyChainAddr) constant returns(uint256) {
        address addr = reverseViewlyClaims[viewlyChainAddr];
        assert(addr != 0x0);
        return viewlyClaims[addr].amount;
    }


    // ---------------
    // ADMIN FUNCTIONS
    // ---------------

    // if something goes horribly wrong, freeze the token
    function freeze() auth {
        VIEW.stop();
    }

    // Side effect of this call is that in finalizeSale(), new maintainer's
    // address will be used as a temporary store of reservedTokens.
    // This shouldn't be a problem, since the tokens are transferred to the
    // multisig account atomically.
    function changeMaintainer(address maintainer) auth note {
        return super.setOwner(maintainer);
    }

}
