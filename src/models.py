"""Data models for nof1.ai scraper"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TradingDecision(BaseModel):
    """Trading decision from the model"""
    symbol: str
    action: str  # HOLD, BUY, SELL
    confidence: float
    quantity: Optional[float] = None


class ModelMessage(BaseModel):
    """Complete message from a trading model"""
    model_name: str
    timestamp: datetime
    message_id: str = Field(default_factory=lambda: f"{datetime.now().isoformat()}")

    # User prompt data
    user_prompt: str
    market_data: Dict[str, Any] = Field(default_factory=dict)

    # Chain of thought
    chain_of_thought: str

    # Trading decisions
    trading_decisions: List[TradingDecision] = Field(default_factory=list)

    # Metadata
    account_value: Optional[float] = None
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    # Storage metadata
    scraped_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_openmemory_content(self) -> str:
        """Format for OpenMemory storage"""
        return f"""
Model: {self.model_name}
Timestamp: {self.timestamp.isoformat()}
Account Value: ${self.account_value:,.2f} ({self.total_return:+.2f}% return)

CHAIN OF THOUGHT:
{self.chain_of_thought}

DECISIONS:
{self._format_decisions()}
"""

    def _format_decisions(self) -> str:
        """Format trading decisions for text output"""
        if not self.trading_decisions:
            return "No trades"

        lines = []
        for decision in self.trading_decisions:
            lines.append(
                f"- {decision.symbol}: {decision.action} "
                f"({decision.confidence:.0%} confidence)"
            )
        return "\n".join(lines)

    def to_metadata(self) -> Dict[str, Any]:
        """Generate metadata for OpenMemory"""
        return {
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "account_value": self.account_value,
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "symbols": [d.symbol for d in self.trading_decisions],
            "actions": [d.action for d in self.trading_decisions],
        }

    def to_tags(self) -> List[str]:
        """Generate tags for OpenMemory"""
        tags = [
            self.model_name.lower().replace(" ", "_"),
            f"date_{self.timestamp.strftime('%Y_%m_%d')}",
        ]

        # Add symbol tags
        for decision in self.trading_decisions:
            tags.append(f"symbol_{decision.symbol.lower()}")
            tags.append(f"action_{decision.action.lower()}")

        return tags


class ScrapeResult(BaseModel):
    """Result of a scraping operation"""
    success: bool
    messages_scraped: int
    messages_stored: int
    errors: List[str] = Field(default_factory=list)
    start_time: datetime
    end_time: datetime

    @property
    def duration_seconds(self) -> float:
        """Calculate scrape duration"""
        return (self.end_time - self.start_time).total_seconds()
