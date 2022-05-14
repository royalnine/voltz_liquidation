// SPDX-License-Identifier: MIT

pragma solidity =0.8.9;

import "../interfaces/ILiquidationBot.sol";

contract LiquidationBot is ILiquidationBot {
    address public marginEngineAddress;

    constructor() {}

    // TODO sort out payable and sending eth across

    function setMarginEngineAddress(address _marginEngineAddress) external {
        // in order to restrict this function to only be callable by the owner of the bot you can apply the onlyOwner modifier by OZ
        require(_marginEngineAddress != address(0), "margin engine address has to be set");
        require(
            (marginEngineAddress != _marginEngineAddress),
            "margin engine already set to this address"
        );
        marginEngineAddress = _marginEngineAddress;
    }

    function getLiquidationReward() external view returns (uint256){
        require(marginEngineAddress != address(0), "margin engine address has to be set");
        // make a call to marginEngine.liquidatorRewardWad()
        (bool success, bytes memory returnData) = marginEngineAddress.staticcall(abi.encodeWithSignature("liquidatorRewardWad()"));

        require(success, "call marginEngine.liquidatorRewardWad() failed");
        (uint liquidationReward) = abi.decode(returnData, (uint));

        return liquidationReward;
    }

    function liquidatePosition(
        address _owner,
        int24 _tickLower,
        int24 _tickUpper
    ) external returns (uint256) {
        require(marginEngineAddress != address(0), "margin engine address has to be set");
        // make a call to marginEngine.liquidatePosition(_owner, _tickLower, _tickUpper);
        (bool success, bytes memory returnData) = marginEngineAddress.call(abi.encodeWithSignature("liquidatePosition(_owner, _tickLower, _tickUpper)", _owner, _tickLower, _tickUpper));
        
        require(success, "call marginEngine.liquidatePosition(_owner, _tickLower, _tickUpper) failed");
        (uint liquidationReward) = abi.decode(returnData, (uint));

        return liquidationReward;
    }

}