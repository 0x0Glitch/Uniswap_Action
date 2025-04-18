"""Schemas for Uniswap V3 action provider."""

from typing import Literal

from pydantic import BaseModel, Field


class CreateLiquiditySchema(BaseModel):
    """Input schema for creating liquidity on Uniswap V3."""

    amount_weth: str = Field(
        ...,
        description="The amount of WETH to deposit, in human-readable format (e.g., '0.5')",
    )
    amount_usdc: str = Field(
        ...,
        description="The amount of USDC to deposit, in human-readable format (e.g., '1000')",
    )
    tick_lower: int = Field(
        ...,
        description="The lower tick boundary of the position. Typically a negative value (e.g., -60000)",
    )
    tick_upper: int = Field(
        ...,
        description="The upper tick boundary of the position. Typically a positive value (e.g., 60000)",
    )
    fee_tier: int = Field(
        3000,
        description="The fee tier to use (500 = 0.05%, 3000 = 0.3%, 10000 = 1%). Default is 0.3% (3000)",
    )
    slippage: float = Field(
        0.5,
        description="Maximum allowed slippage in percentage (e.g., 0.5 for 0.5%). Default is 0.5%",
    )


class GetPriceSchema(BaseModel):
    """Input schema for fetching current WETH/USDC price from Uniswap V3."""
    fee_tier: int = Field(
        3000,
        description="The fee tier to use (500 = 0.05%, 3000 = 0.3%, 10000 = 1%). Default is 0.3% (3000)",
    )
