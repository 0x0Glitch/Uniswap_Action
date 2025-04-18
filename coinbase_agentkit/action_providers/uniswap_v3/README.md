# Uniswap V3 Action Provider

This directory contains the **UniswapV3ActionProvider** implementation, which provides actions to interact with **Uniswap V3 Protocol** for creating and managing liquidity positions.

## Directory Structure

```
uniswap_v3/
├── uniswap_v3_action_provider.py  # Uniswap V3 action provider
├── constants.py                  # Constants like ABIs and addresses
├── schemas.py                    # Action schemas
├── utils.py                      # Helper functions
├── __init__.py                   # Main exports
└── README.md                     # This file
```

## Actions

These actions allow you to create and manage liquidity positions on Uniswap V3 protocol:

- `create_liquidity`: Creates a liquidity position for WETH/USDC pair on Uniswap V3 with specified price range.

## Usage

```python
from coinbase_agentkit import AgentKit, AgentKitConfig, uniswap_v3_action_provider

# Create AgentKit instance with Uniswap V3 action provider
agent_kit = AgentKit(AgentKitConfig(
    action_providers=[uniswap_v3_action_provider()]
))

# Create liquidity position
result = agent_kit.execute_action(
    action_name="uniswap-v3.create_liquidity",
    action_args={
        "amount_weth": "0.1",
        "amount_usdc": "200",
        "tick_lower": -60000,
        "tick_upper": 60000,
        "fee_tier": 3000,  # 0.3%
        "slippage": 0.5
    }
)
```

## Notes

### Tick Ranges and Price Calculation

Uniswap V3 uses ticks to represent price ranges. The relationship between tick and price is:

```
price = 1.0001^tick
```

Common tick ranges:
- Full range: -887272 to 887272
- Typical WETH/USDC range: -60000 to 60000

### Fee Tiers

Uniswap V3 supports multiple fee tiers:
- 500 = 0.05%
- 3000 = 0.3% (default)
- 10000 = 1%

Higher fee tiers are suitable for more volatile pairs, while lower fee tiers work better for stable pairs.

### Supported Networks

Currently only supports the following networks:
- Base Mainnet

### Limitations

- Currently only supports WETH/USDC pair
- You need to have both WETH and USDC tokens in your wallet before creating a position
- The position is created as an NFT in your wallet
