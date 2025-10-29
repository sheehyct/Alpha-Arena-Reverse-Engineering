"""Chain of thought extraction from nof1.ai message structure"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from rich.console import Console

from .models import ModelMessage, TradingDecision

console = Console()


class ChainExtractor:
    """Extracts chain of thought data from nof1.ai message elements"""

    def extract_from_snapshot(self, snapshot_data: Dict[str, Any]) -> Optional[ModelMessage]:
        """
        Extract message data from Playwright browser snapshot

        The snapshot structure from nof1.ai looks like:
        - Model name + timestamp header
        - USER_PROMPT section (expandable)
        - CHAIN_OF_THOUGHT section (expandable)
        - TRADING_DECISIONS section (expandable)

        Args:
            snapshot_data: Data structure from the expanded message

        Returns:
            ModelMessage if extraction successful, None otherwise
        """
        try:
            # Extract model name and timestamp from header
            model_name = self._extract_model_name(snapshot_data)
            timestamp = self._extract_timestamp(snapshot_data)

            if not model_name or not timestamp:
                console.print("[yellow]Could not extract model name or timestamp[/yellow]")
                return None

            # Extract sections
            user_prompt = self._extract_section(snapshot_data, "USER_PROMPT")
            chain_of_thought = self._extract_section(snapshot_data, "CHAIN_OF_THOUGHT")
            trading_decisions_text = self._extract_section(snapshot_data, "TRADING_DECISIONS")

            if not chain_of_thought:
                console.print("[yellow]Could not extract chain of thought[/yellow]")
                return None

            # Parse trading decisions
            trading_decisions = self._parse_trading_decisions(trading_decisions_text)

            # Extract account metrics from user prompt
            account_value, total_return, sharpe_ratio = self._extract_account_metrics(
                user_prompt
            )

            # Parse market data if available
            market_data = self._extract_market_data(user_prompt)

            return ModelMessage(
                model_name=model_name,
                timestamp=timestamp,
                user_prompt=user_prompt,
                market_data=market_data,
                chain_of_thought=chain_of_thought,
                trading_decisions=trading_decisions,
                account_value=account_value,
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
            )

        except Exception as e:
            console.print(f"[red]Error extracting message: {e}[/red]")
            return None

    def _extract_model_name(self, snapshot_data: Dict[str, Any]) -> Optional[str]:
        """Extract model name from snapshot header"""
        # Model name is typically in a heading element
        # Look for patterns like "CLAUDE SONNET 4.5", "GPT 5", etc.
        text = str(snapshot_data)

        # Common model name patterns
        model_patterns = [
            r"CLAUDE SONNET 4\.5",
            r"DEEPSEEK CHAT V3\.1",
            r"GEMINI 2\.5 PRO",
            r"GPT 5",
            r"GROK 4",
            r"QWEN3 MAX",
        ]

        for pattern in model_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).title()

        return None

    def _extract_timestamp(self, snapshot_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from snapshot"""
        text = str(snapshot_data)

        # Look for timestamp pattern: "10/29 07:57:57"
        timestamp_pattern = r"(\d{1,2})/(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})"
        match = re.search(timestamp_pattern, text)

        if match:
            month, day, hour, minute, second = map(int, match.groups())
            # Assume current year
            year = datetime.now().year

            return datetime(year, month, day, hour, minute, second)

        return None

    def _extract_section(self, snapshot_data: Dict[str, Any], section_name: str) -> str:
        """
        Extract a specific section from the snapshot

        Args:
            snapshot_data: The snapshot data structure
            section_name: Name of section (USER_PROMPT, CHAIN_OF_THOUGHT, TRADING_DECISIONS)

        Returns:
            Extracted text content
        """
        text = str(snapshot_data)

        # Find the section header and extract content until next section
        section_pattern = rf"{section_name}.*?(?=▶|$)"
        match = re.search(section_pattern, text, re.DOTALL)

        if match:
            content = match.group(0)
            # Clean up the content
            content = re.sub(r"▶\s*" + section_name, "", content)
            return content.strip()

        return ""

    def _parse_trading_decisions(self, decisions_text: str) -> List[TradingDecision]:
        """
        Parse trading decisions from text

        Expected format:
        SOL
        HOLD
        65%
        QUANTITY: 25.7
        """
        decisions = []

        # Pattern to match decision blocks
        # Looking for: Symbol, Action, Confidence, Quantity
        pattern = r"([A-Z]+)\s+(HOLD|BUY|SELL)\s+(\d+)%\s+QUANTITY:\s+([\d.]+)"

        for match in re.finditer(pattern, decisions_text):
            symbol, action, confidence, quantity = match.groups()

            decisions.append(
                TradingDecision(
                    symbol=symbol,
                    action=action,
                    confidence=float(confidence) / 100.0,
                    quantity=float(quantity) if quantity else None,
                )
            )

        return decisions

    def _extract_account_metrics(self, user_prompt: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Extract account value, total return, and sharpe ratio from user prompt

        Expected patterns:
        - Current Account Value: 10076.35
        - Current Total Return (percent): 0.76%
        - Sharpe Ratio: 0.033
        """
        account_value = None
        total_return = None
        sharpe_ratio = None

        # Extract account value
        value_match = re.search(r"Current Account Value:\s*([\d,.]+)", user_prompt)
        if value_match:
            account_value = float(value_match.group(1).replace(",", ""))

        # Extract total return
        return_match = re.search(r"Current Total Return.*?:\s*([-+]?[\d.]+)%", user_prompt)
        if return_match:
            total_return = float(return_match.group(1))

        # Extract sharpe ratio
        sharpe_match = re.search(r"Sharpe Ratio:\s*([-+]?[\d.]+)", user_prompt)
        if sharpe_match:
            sharpe_ratio = float(sharpe_match.group(1))

        return account_value, total_return, sharpe_ratio

    def _extract_market_data(self, user_prompt: str) -> Dict[str, Any]:
        """
        Extract market data from user prompt

        This includes price data, indicators, etc. for each coin
        """
        market_data = {}

        # Extract data for each coin
        coin_symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"]

        for symbol in coin_symbols:
            # Look for section headers like "ALL BTC DATA"
            section_pattern = rf"ALL {symbol} DATA.*?(?=ALL [A-Z]+ DATA|HERE IS YOUR ACCOUNT|$)"
            match = re.search(section_pattern, user_prompt, re.DOTALL)

            if match:
                section_text = match.group(0)

                # Extract key metrics
                coin_data = {}

                # Current price
                price_match = re.search(r"current_price\s*=\s*([\d.]+)", section_text)
                if price_match:
                    coin_data["current_price"] = float(price_match.group(1))

                # MACD
                macd_match = re.search(r"current_macd\s*=\s*([-\d.]+)", section_text)
                if macd_match:
                    coin_data["current_macd"] = float(macd_match.group(1))

                # RSI
                rsi_match = re.search(r"current_rsi.*?=\s*([\d.]+)", section_text)
                if rsi_match:
                    coin_data["current_rsi"] = float(rsi_match.group(1))

                if coin_data:
                    market_data[symbol] = coin_data

        return market_data
