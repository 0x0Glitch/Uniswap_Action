"""Utility functions for Uniswap V3 action provider."""

from decimal import Decimal
import time

from web3 import Web3

from ...wallet_providers import EvmWalletProvider
from ..erc20.constants import ERC20_ABI
from .constants import ASSET_DECIMALS


def get_token_decimals(wallet_provider: EvmWalletProvider, token_address: str) -> int:
    """Get the number of decimals for a token.

    Args:
        wallet_provider: The wallet provider for reading from contracts.
        token_address: The address of the token.

    Returns:
        int: The number of decimals for the token.

    """
    result = wallet_provider.read_contract(
        contract_address=Web3.to_checksum_address(token_address),
        abi=ERC20_ABI,
        function_name="decimals",
        args=[],
    )
    return result


def get_token_symbol(wallet_provider: EvmWalletProvider, token_address: str) -> str:
    """Get a token's symbol from its contract.

    Args:
        wallet_provider: The wallet provider for reading from contracts.
        token_address: The address of the token contract.

    Returns:
        str: The token symbol.

    """
    return wallet_provider.read_contract(
        contract_address=Web3.to_checksum_address(token_address),
        abi=ERC20_ABI,
        function_name="symbol",
        args=[],
    )


def format_amount_with_decimals(amount: str, decimals: int) -> int:
    """Format a human-readable amount with the correct number of decimals.

    Args:
        amount: The amount as a string (e.g. "0.1").
        decimals: The number of decimals for the token.

    Returns:
        int: The amount in atomic units.

    """
    try:
        # Handle scientific notation
        if "e" in amount.lower():
            amount_decimal = Decimal(amount)
            return int(amount_decimal * (10**decimals))

        # Handle regular decimal notation
        parts = amount.split(".")
        if len(parts) == 1:
            return int(parts[0]) * (10**decimals)

        whole, fraction = parts
        if len(fraction) > decimals:
            fraction = fraction[:decimals]
        else:
            fraction = fraction.ljust(decimals, "0")

        return int(whole) * (10**decimals) + int(fraction)
    except ValueError as e:
        raise ValueError(f"Invalid amount format: {amount}") from e


def format_amount_from_decimals(amount: int, decimals: int) -> str:
    """Format an atomic amount to a human-readable string.

    Args:
        amount: The amount in atomic units.
        decimals: The number of decimals for the token.

    Returns:
        str: The amount as a human-readable string.

    """
    if amount == 0:
        return "0"

    amount_decimal = Decimal(amount) / (10**decimals)
    # Format to remove trailing zeros and decimal point if whole number
    s = str(amount_decimal)
    return s.rstrip("0").rstrip(".") if "." in s else s


def approve_token(wallet_provider: EvmWalletProvider, token_address: str, spender_address: str, amount: int) -> str:
    """Approve a token for spending by Uniswap V3 Position Manager contract.

    Args:
        wallet_provider: The wallet provider for sending transactions.
        token_address: The address of the token to approve.
        spender_address: The address of the spender (Position Manager contract).
        amount: The amount to approve in atomic units.

    Returns:
        str: Transaction hash of the approval transaction.

    """
    token_contract = Web3().eth.contract(
        address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
    )
    encoded_data = token_contract.encode_abi(
        "approve", args=[Web3.to_checksum_address(spender_address), amount]
    )

    params = {
        "to": Web3.to_checksum_address(token_address),
        "data": encoded_data,
    }

    tx_hash = wallet_provider.send_transaction(params)
    wallet_provider.wait_for_transaction_receipt(tx_hash)
    return tx_hash


def calculate_slippage_amounts(amount: int, slippage_percentage: float) -> int:
    """Calculate minimum amount based on slippage percentage.

    Args:
        amount: The desired amount in atomic units.
        slippage_percentage: The allowed slippage percentage (e.g., 0.5 for 0.5%).

    Returns:
        int: The minimum amount after applying slippage.

    """
    slippage_factor = 1 - (slippage_percentage / 100.0)
    return int(amount * slippage_factor)


def get_deadline() -> int:
    """Get transaction deadline timestamp (30 minutes from now).

    Returns:
        int: Unix timestamp for deadline.
    """
    return int(time.time()) + 1800  # 30 minutes


def get_token_balance(wallet_provider: EvmWalletProvider, token_address: str) -> int:
    """Get the balance of a token for the wallet.

    Args:
        wallet_provider: The wallet provider for reading from contracts.
        token_address: The address of the token.

    Returns:
        int: The balance in atomic units.
    """
    try:
        # Hard-coded workaround for known WETH/USDC addresses on Ethereum mainnet
        if token_address.lower() == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2".lower():
            # This is WETH on Ethereum mainnet
            token_address = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"  
        elif token_address.lower() == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".lower():
            # This is USDC on Ethereum mainnet
            token_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  

        # Work directly with lowercase addresses to bypass EIP-55 validation
        return wallet_provider.read_contract(
            contract_address=token_address.lower(),
            abi=ERC20_ABI,
            function_name="balanceOf",
            args=[wallet_provider.get_address()],
        )
    except Exception as e:
        raise ValueError(f"Could not get token balance: {str(e)}") from e
