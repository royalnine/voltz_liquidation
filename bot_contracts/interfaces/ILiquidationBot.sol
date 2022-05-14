// SPDX-License-Identifier: Apache-2.0

pragma solidity =0.8.9;


interface ILiquidationBot{

    function setMarginEngineAddress(address _marginEngineAddress) external;

    function getLiquidationReward() external view returns (uint256);

    function liquidatePosition(address _owner, int24 _tickLower, int24 _tickUpper) external returns (uint256);

}