# Uniswap V3 Action Provider

This repository contains a Uniswap V3 Action Provider for interacting with Uniswap V3 protocol on Ethereum mainnet. The provider allows for creating liquidity positions on the WETH/USDC pool.

## Features

- Create liquidity positions on Uniswap V3 for WETH/USDC pair
- Support for different fee tiers (0.05%, 0.3%, 1%)
- Proper tick spacing alignment based on fee tier
- Slippage protection
- Token approval handling

## Key Components

- `uniswap_v3_action_provider.py`: Main action provider implementation
- `constants.py`: Contract addresses and ABIs
- `schemas.py`: Input validation schemas
- `utils.py`: Helper functions for token interactions

## Usage

The action provider includes a `create_liquidity` function that takes the following parameters:

- `amount_weth`: The amount of WETH to deposit (human-readable format)
- `amount_usdc`: The amount of USDC to deposit (human-readable format)
- `tick_lower`: The lower tick boundary
- `tick_upper`: The upper tick boundary
- `fee_tier`: (Optional) Fee tier to use (500=0.05%, 3000=0.3%, 10000=1%)
- `slippage`: (Optional) Maximum allowed slippage percentage

## Implementation Notes

- Token ordering is handled automatically (USDC as token0, WETH as token1)
- Tick values are automatically aligned to the appropriate spacing for the fee tier
- Transaction parameters include explicit gas limits to prevent estimation errors
