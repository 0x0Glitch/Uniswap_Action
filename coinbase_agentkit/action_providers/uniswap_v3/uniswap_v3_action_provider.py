"""Uniswap V3 action provider for interacting with Uniswap V3 protocol."""

from typing import Any

from web3 import Web3

from ...network import Network
from ...wallet_providers import EvmWalletProvider
from ..action_decorator import create_action
from ..action_provider import ActionProvider
from .constants import (
    ASSET_ADDRESSES,
    ASSET_DECIMALS,
    POSITION_MANAGER_ADDRESSES,
    SUPPORTED_NETWORKS,
    UNISWAP_V3_POSITION_MANAGER_ABI,
    UNISWAP_V3_FACTORY_ADDRESS,
    UNISWAP_V3_FACTORY_ABI,
    UNISWAP_V3_POOL_ABI,
)
from .schemas import CreateLiquiditySchema, GetPriceSchema
from .utils import (
    approve_token,
    calculate_slippage_amounts,
    format_amount_from_decimals,
    format_amount_with_decimals,
    get_deadline,
    get_token_balance,
    get_token_symbol,
)


class UniswapV3ActionProvider(ActionProvider[EvmWalletProvider]):
    """Provides actions for interacting with Uniswap V3 protocol."""

    def __init__(self):
        """Initialize the Uniswap V3 action provider."""
        super().__init__("uniswap-v3", [])

    def supports_network(self, network: Network) -> bool:
        """Check if network is supported by Uniswap V3 actions.

        Args:
            network: The network to check.

        Returns:
            bool: True if the network is supported.

        """
        # Check for Ethereum mainnet (various possible network_id variations)
        is_mainnet = (network.chain_id == "1" or 
                     network.network_id in ["mainnet", "ethereum-mainnet"])
        
        return network.protocol_family == "evm" and is_mainnet

    def _get_position_manager_address(self, network: Network) -> str:
        """Get the appropriate Uniswap V3 Position Manager address based on network.

        Args:
            network: The network to get address for.

        Returns:
            str: The appropriate Uniswap V3 Position Manager address.

        Raises:
            ValueError: If no address available for the network.
        """
        # Handle Ethereum mainnet with different possible network IDs
        if network.chain_id == "1":
            # Use the ethereum-mainnet key regardless of what the network ID is reported as
            return POSITION_MANAGER_ADDRESSES["ethereum-mainnet"]
        elif network.network_id in POSITION_MANAGER_ADDRESSES:
            return POSITION_MANAGER_ADDRESSES[network.network_id]
        else:
            raise ValueError(f"No Position Manager address available for network {network.network_id}")

    def _get_asset_address(self, network: Network, asset_id: str) -> str:
        """Get the asset address based on network and asset ID."""
        try:
            # For Ethereum mainnet, always use the ethereum-mainnet key
            if network.chain_id == "1":
                return ASSET_ADDRESSES["ethereum-mainnet"][asset_id]
            else:
                return ASSET_ADDRESSES[network.network_id][asset_id]
        except KeyError as err:
            raise ValueError(f"Asset {asset_id} not supported on {network.network_id}") from err

    @create_action(
        name="create_liquidity",
        description="""
This tool creates a liquidity position on Uniswap V3 for WETH/USDC pair.
It takes:
- amount_weth: The amount of WETH to deposit (in human-readable format e.g., '0.5')
- amount_usdc: The amount of USDC to deposit (in human-readable format e.g., '1000')
- tick_lower: The lower tick boundary (typically negative, e.g., -60000)
- tick_upper: The upper tick boundary (typically positive, e.g., 60000)
- fee_tier: (Optional) Fee tier to use (500=0.05%, 3000=0.3%, 10000=1%). Default is 0.3%
- slippage: (Optional) Maximum allowed slippage percentage. Default is 0.5%

Important notes:
- Make sure you have both WETH and USDC tokens in your wallet
- The tick values determine the price range for your position
- A wider tick range (e.g., -60000 to 60000) collects less fees but works in more market conditions
- A narrower tick range collects more fees but may go out of range more quickly
- The position will be a non-fungible token (NFT) in your wallet
""",
        schema=CreateLiquiditySchema,
    )
    def create_liquidity(self, wallet_provider: EvmWalletProvider, args: dict[str, Any]) -> str:
        """Create a liquidity position on Uniswap V3.

        Args:
            wallet_provider: The wallet to use for the create_liquidity operation.
            args: The input arguments for the create_liquidity operation.

        Returns:
            str: A message containing the result of the create_liquidity operation.

        """
        try:
            validated_args = CreateLiquiditySchema(**args)
            network = wallet_provider.get_network()

            # Check if the network is supported
            if not self.supports_network(network):
                return f"Error: Network {network.network_id} is not supported by Uniswap V3"

            try:
                position_manager_address = self._get_position_manager_address(network)
            except Exception as e:
                return f"Error: Could not get Uniswap V3 Position Manager address for {network.network_id}: {e!s}"

            # Get token addresses
            try:
                weth_address = self._get_asset_address(network, "weth")
                usdc_address = self._get_asset_address(network, "usdc")
            except ValueError as e:
                return f"Error: {e!s}"
            except Exception as e:
                return f"Error: Could not get asset addresses on {network.network_id}: {e!s}"

            # Convert human-readable amounts to token units
            weth_decimals = ASSET_DECIMALS["weth"]
            usdc_decimals = ASSET_DECIMALS["usdc"]
            amount_weth_units = format_amount_with_decimals(validated_args.amount_weth, weth_decimals)
            amount_usdc_units = format_amount_with_decimals(validated_args.amount_usdc, usdc_decimals)

            # Check wallet balances
            weth_balance = get_token_balance(wallet_provider, weth_address)
            usdc_balance = get_token_balance(wallet_provider, usdc_address)

            if weth_balance < amount_weth_units:
                weth_formatted = format_amount_from_decimals(weth_balance, weth_decimals)
                return f"Error: Insufficient WETH balance. You have {weth_formatted} WETH, but need {validated_args.amount_weth} WETH"

            if usdc_balance < amount_usdc_units:
                usdc_formatted = format_amount_from_decimals(usdc_balance, usdc_decimals)
                return f"Error: Insufficient USDC balance. You have {usdc_formatted} USDC, but need {validated_args.amount_usdc} USDC"

            # Calculate minimum amounts with slippage
            amount_weth_min = calculate_slippage_amounts(amount_weth_units, validated_args.slippage)
            amount_usdc_min = calculate_slippage_amounts(amount_usdc_units, validated_args.slippage)

            # Approve tokens for the position manager
            try:
                # Get balances
                weth_balance = get_token_balance(wallet_provider, weth_address)
                usdc_balance = get_token_balance(wallet_provider, usdc_address)

                # Format amounts and log for debugging
                weth_balance_formatted = format_amount_from_decimals(weth_balance, weth_decimals)
                usdc_balance_formatted = format_amount_from_decimals(usdc_balance, usdc_decimals)

                # Log balances for debugging
                print(f"WETH balance: {weth_balance_formatted} WETH, USDC balance: {usdc_balance_formatted} USDC")
                print(f"WETH needed: {validated_args.amount_weth}, USDC needed: {validated_args.amount_usdc}")

                _ = approve_token(
                    wallet_provider, weth_address, position_manager_address, amount_weth_units
                )
            except Exception as e:
                # Enhanced error logging
                import traceback
                error_details = traceback.format_exc()
                detailed_error = f"Error creating Uniswap V3 liquidity position: {e!s}\n\nDetailed traceback:\n{error_details}"
                print(detailed_error)  # Print to console for debugging
                return f"Error creating Uniswap V3 liquidity position: {e!s}\nTry using ticks that align with 0.05% fee tier spacing (10): tickLower=202540, tickUpper=202640"

            try:
                _ = approve_token(
                    wallet_provider, usdc_address, position_manager_address, amount_usdc_units
                )
            except Exception as e:
                # Enhanced error logging
                import traceback
                error_details = traceback.format_exc()
                detailed_error = f"Error creating Uniswap V3 liquidity position: {e!s}\n\nDetailed traceback:\n{error_details}"
                print(detailed_error)  # Print to console for debugging
                return f"Error creating Uniswap V3 liquidity position: {e!s}\nTry using ticks that align with 0.05% fee tier spacing (10): tickLower=202540, tickUpper=202640"

            # Based on mainnet addresses, USDC (0xA0b8...) < WETH (0xC02a...)
            # Therefore USDC is always token0 and WETH is token1
            token0, token1 = usdc_address, weth_address
            amount0Desired, amount1Desired = amount_usdc_units, amount_weth_units
            amount0Min, amount1Min = amount_usdc_min, amount_weth_min

            # Create mint params for the position
            # Get the web3 instance from the wallet provider
            web3_instance = wallet_provider.web3
            
            # Determine tick spacing based on fee tier
            fee_tier = validated_args.fee_tier
            if fee_tier == 500:
                tick_spacing = 10   # 0.05% fee tier
            elif fee_tier == 3000:
                tick_spacing = 60   # 0.3% fee tier
            elif fee_tier == 10000:
                tick_spacing = 200  # 1% fee tier
            else:
                # Default to 0.05% fee tier
                tick_spacing = 10
                fee_tier = 500
                print(f"Warning: Unsupported fee tier {validated_args.fee_tier}, defaulting to 0.05% (500)")
            
            lower_tick = validated_args.tick_lower
            upper_tick = validated_args.tick_upper
            
            # Round to the nearest valid tick
            lower_tick = (lower_tick // tick_spacing) * tick_spacing
            upper_tick = (upper_tick // tick_spacing) * tick_spacing
            
            # Ensure upper tick is strictly greater than lower tick
            if upper_tick <= lower_tick:
                upper_tick = lower_tick + tick_spacing
                
            contract = web3_instance.eth.contract(
                address=Web3.to_checksum_address(position_manager_address),
                abi=UNISWAP_V3_POSITION_MANAGER_ABI,
            )

            # Create a tuple of params instead of a dict - the ABI expects a tuple
            deadline = get_deadline()
            recipient = wallet_provider.get_address()
            
            # Create the mint parameters tuple in the expected order
            mint_tuple = (
                Web3.to_checksum_address(token0),
                Web3.to_checksum_address(token1),
                fee_tier,
                lower_tick,
                upper_tick,
                amount0Desired,
                amount1Desired,
                amount0Min,  # Use calculated slippage value
                amount1Min,  # Use calculated slippage value
                recipient,
                deadline
            )
            
            # Call mint with the tuple parameters
            fn = contract.functions.mint(mint_tuple)
            encoded_data = fn._encode_transaction_data()

            params = {
                "to": Web3.to_checksum_address(position_manager_address),
                "data": encoded_data,
                "gas": 3000000,  # Higher gas limit for complex contract interactions
                # Let the wallet provider handle the gas pricing
            }

            # Add debug logging
            print(f"Transaction parameters:\n"
                  f"- To: {position_manager_address}\n"
                  f"- Token0: {token0}\n"
                  f"- Token1: {token1}\n"
                  f"- Fee: {fee_tier}\n"
                  f"- TickLower: {lower_tick} (rounded to fee tier spacing)\n"
                  f"- TickUpper: {upper_tick} (rounded to fee tier spacing)\n"
                  f"- Amount0: {amount0Desired}\n"
                  f"- Amount1: {amount1Desired}\n"
                  f"- Slippage: {validated_args.slippage}%\n"
                  f"- Deadline: {get_deadline()}")

            try:
                tx_hash = wallet_provider.send_transaction(params)
                receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)

                if receipt.status != 1:
                    return f"Error: Liquidity position creation failed. Transaction hash: {tx_hash}"

                # Try to extract the token ID from the transaction logs
                token_id = None
                for log in receipt.logs:
                    if log["address"].lower() == position_manager_address.lower() and len(log["topics"]) > 3:
                        # This is likely the Transfer event for the new NFT
                        token_id = int(log["topics"][3].hex(), 16)
                        break

                token_id_msg = f"\nPosition NFT ID: {token_id}" if token_id else ""

                return (
                    f"Successfully created Uniswap V3 liquidity position with:\n"
                    f"- {validated_args.amount_weth} WETH\n"
                    f"- {validated_args.amount_usdc} USDC\n"
                    f"- Price range ticks: {lower_tick} to {upper_tick} (aligned with fee tier spacing)\n"
                    f"- Fee tier: {fee_tier}\n"
                    f"Transaction hash: {tx_hash}{token_id_msg}"
                )

            except Exception as e:
                # Enhanced error logging
                import traceback
                error_details = traceback.format_exc()
                detailed_error = f"Error creating Uniswap V3 liquidity position: {e!s}\n\nDetailed traceback:\n{error_details}"
                print(detailed_error)  # Print to console for debugging
                return f"Error creating Uniswap V3 liquidity position: {e!s}\nTry using ticks that align with 0.05% fee tier spacing (10): tickLower=202540, tickUpper=202640"

        except Exception as e:
            # Enhanced error logging
            import traceback
            error_details = traceback.format_exc()
            detailed_error = f"Error creating Uniswap V3 liquidity position: {e!s}\n\nDetailed traceback:\n{error_details}"
            print(detailed_error)  # Print to console for debugging
            return f"Error creating Uniswap V3 liquidity position: {e!s}\nTry using ticks that align with 0.05% fee tier spacing (10): tickLower=202540, tickUpper=202640"

    @create_action(
        name="get_price",
        description="""Fetch current WETH/USDC price from Uniswap V3 pool for a given fee tier.""",
        schema=GetPriceSchema,
    )
    def get_price(self, wallet_provider: EvmWalletProvider, args: dict[str, Any]) -> str:
        """Fetch the current WETH/USDC price."""
        validated_args = GetPriceSchema(**args)
        network = wallet_provider.get_network()
        if not self.supports_network(network):
            return f"Error: Network {network.network_id} is not supported by Uniswap V3"
        try:
            weth_address = self._get_asset_address(network, "weth")
            usdc_address = self._get_asset_address(network, "usdc")
        except Exception as e:
            return f"Error: Could not get asset addresses: {e!s}"
        factory_address = Web3.to_checksum_address(UNISWAP_V3_FACTORY_ADDRESS[network.network_id])
        try:
            pool_address = wallet_provider.read_contract(
                contract_address=factory_address,
                abi=UNISWAP_V3_FACTORY_ABI,
                function_name="getPool",
                args=[
                    Web3.to_checksum_address(weth_address),
                    Web3.to_checksum_address(usdc_address),
                    validated_args.fee_tier
                ],
            )
        except Exception as e:
            return f"Error: Failed to fetch pool address: {e!s}"
        if pool_address == "0x0000000000000000000000000000000000000000":
            return f"Error: No pool found for fee tier {validated_args.fee_tier}"
        pool_address = Web3.to_checksum_address(pool_address)
        try:
            slot0 = wallet_provider.read_contract(
                contract_address=pool_address,
                abi=UNISWAP_V3_POOL_ABI,
                function_name="slot0",
                args=[],
            )
        except Exception as e:
            return f"Error fetching pool state (slot0): {e!s}"
        sqrt_price_x96, current_tick = slot0[0], slot0[1]
        decimals_weth = ASSET_DECIMALS["weth"]
        decimals_usdc = ASSET_DECIMALS["usdc"]
        price_ratio = (sqrt_price_x96 / (2**96)) ** 2
        price = price_ratio * (10 ** (decimals_weth - decimals_usdc))
        return f"Current WETH/USDC price: {price:.6f} USDC per WETH (tick: {current_tick})"


def uniswap_v3_action_provider() -> UniswapV3ActionProvider:
    """Create a new UniswapV3ActionProvider instance.

    Returns:
        UniswapV3ActionProvider: A new instance of the Uniswap V3 action provider.

    """
    return UniswapV3ActionProvider()
