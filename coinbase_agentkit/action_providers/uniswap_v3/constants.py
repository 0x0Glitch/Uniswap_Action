"""Constants for Uniswap V3 action provider – Ethereum Mainnet"""

from web3 import Web3

# === 1. Supported network key must match wallet_provider.get_network().network_id
SUPPORTED_NETWORKS = ["ethereum-mainnet"]

# === 2. Canonical contract addresses ===
POSITION_MANAGER_ADDRESSES = {
    "ethereum-mainnet": Web3.to_checksum_address(
        "0xc36442b4a4522e871399cd717abdd847ab11fe88"  # NonfungiblePositionManager
    )
}

ASSET_ADDRESSES = {
    "ethereum-mainnet": {
        # supply lower‑case literal → let Web3 produce correct checksum
        "weth": Web3.to_checksum_address(
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        ),
        "usdc": Web3.to_checksum_address(
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        ),
    }
}

ASSET_DECIMALS = {"weth": 18, "usdc": 6}

UNISWAP_V3_FACTORY_ADDRESS = {
    "ethereum-mainnet": Web3.to_checksum_address(
        "0x1f98431c8ad98523631ae4a59f267346ea31f984"
    )
}

# Factory ABI to fetch pool address
UNISWAP_V3_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24",   "name": "fee",    "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [
            {"internalType": "address", "name": "pool", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# ABI for Uniswap V3 pool slot0
UNISWAP_V3_POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24",   "name": "",             "type": "int24"},
            {"internalType": "uint16",  "name": "",             "type": "uint16"},
            {"internalType": "uint16",  "name": "",             "type": "uint16"},
            {"internalType": "uint16",  "name": "",             "type": "uint16"},
            {"internalType": "uint8",   "name": "",             "type": "uint8"},
            {"internalType": "bool",    "name": "",             "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# ABI fragment for the Uniswap V3 NonfungiblePositionManager mint function
UNISWAP_V3_POSITION_MANAGER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "token0", "type": "address"},
                    {"internalType": "address", "name": "token1", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "int24", "name": "tickLower", "type": "int24"},
                    {"internalType": "int24", "name": "tickUpper", "type": "int24"},
                    {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"},
                    {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"},
                    {"internalType": "uint256", "name": "amount0Min", "type": "uint256"},
                    {"internalType": "uint256", "name": "amount1Min", "type": "uint256"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "internalType": "struct INonfungiblePositionManager.MintParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "mint",
        "outputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "positions",
        "outputs": [
            {"internalType": "uint96", "name": "nonce", "type": "uint96"},
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "address", "name": "token0", "type": "address"},
            {"internalType": "address", "name": "token1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
            {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
