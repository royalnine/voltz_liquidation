// SPDX-License-Identifier: MIT

pragma solidity =0.8.9;

import "../interfaces/ILiquidationBot.sol";
import "OpenZeppelin/openzeppelin-contracts@4.5.0/contracts/access/Ownable.sol";


contract LiquidationBot is ILiquidationBot, Ownable {
    address private marginEngineAddress;

    constructor(address _marginEngineAddress) {
        require(_marginEngineAddress != address(0), "margin engine address has to be set");
        marginEngineAddress = _marginEngineAddress;
    }

    function liquidatePosition(
        address _owner,
        int24 _tickLower,
        int24 _tickUpper
    ) external onlyOwner returns (uint256) {
        require(marginEngineAddress != address(0), "margin engine address has to be set");
        // make a call to marginEngine.liquidatePosition(_owner, _tickLower, _tickUpper);
        (bool success, bytes memory returnData) = marginEngineAddress.call(abi.encodeWithSignature("liquidatePosition(address,int24,int24)", _owner, _tickLower, _tickUpper));
        
        require(success, "call marginEngine.liquidatePosition(_owner, _tickLower, _tickUpper) failed");
        (uint liquidationReward) = abi.decode(returnData, (uint));

        return liquidationReward;
    }

    function getPositionMarginRequirement(
        address _owner,
        int24 _tickLower,
        int24 _tickUpper
    ) external returns (uint256){
        require(marginEngineAddress != address(0), "margin engine address has to be set");
        // make a call to marginEngine.liquidatePosition(_owner, _tickLower, _tickUpper);
        (bool success, bytes memory returnData) = marginEngineAddress.call(abi.encodeWithSignature("getPositionMarginRequirement(address,int24,int24,bool)", _owner, _tickLower, _tickUpper, true)); // make static call and catch the error
        
        require(success, "call marginEngine.getPositionMarginRequirement(_owner, _tickLower, _tickUpper, _isLM) failed");
        (uint marginRequirement) = abi.decode(returnData, (uint256));

        return marginRequirement;
    }

}