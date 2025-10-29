"""
SQLite reader for Chrome Extension data
Reads nof1_data.db and converts to ModelMessage format
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import ModelMessage, TradingDecision


class ExtensionDataReader:
    """Reads Chrome extension SQLite database and converts to ModelMessage format"""

    def __init__(self, db_path: Path):
        """
        Initialize reader

        Args:
            db_path: Path to nof1_data.db from Chrome extension
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def read_all_messages(self, model_name: Optional[str] = None) -> List[ModelMessage]:
        """
        Read all messages from database

        Args:
            model_name: Optional filter for specific model

        Returns:
            List of ModelMessage objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if model_name:
            query = """
                SELECT * FROM model_chat
                WHERE model_name = ?
                ORDER BY timestamp DESC
            """
            cursor.execute(query, (model_name,))
        else:
            query = """
                SELECT * FROM model_chat
                ORDER BY timestamp DESC
            """
            cursor.execute(query)

        messages = []
        for row in cursor.fetchall():
            try:
                msg = self._row_to_model_message(row)
                messages.append(msg)
            except Exception as e:
                print(f"Warning: Failed to parse row {row['id']}: {e}")
                continue

        conn.close()
        return messages

    def read_messages_since(self, since: datetime, model_name: Optional[str] = None) -> List[ModelMessage]:
        """
        Read messages since a specific timestamp

        Args:
            since: Only return messages after this time
            model_name: Optional filter for specific model

        Returns:
            List of ModelMessage objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since_iso = since.isoformat()

        if model_name:
            query = """
                SELECT * FROM model_chat
                WHERE model_name = ? AND timestamp > ?
                ORDER BY timestamp DESC
            """
            cursor.execute(query, (model_name, since_iso))
        else:
            query = """
                SELECT * FROM model_chat
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """
            cursor.execute(query, (since_iso,))

        messages = []
        for row in cursor.fetchall():
            try:
                msg = self._row_to_model_message(row)
                messages.append(msg)
            except Exception as e:
                print(f"Warning: Failed to parse row {row['id']}: {e}")
                continue

        conn.close()
        return messages

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total messages
        cursor.execute("SELECT COUNT(*) FROM model_chat")
        total = cursor.fetchone()[0]

        # By model
        cursor.execute("""
            SELECT model_name, COUNT(*) as count
            FROM model_chat
            GROUP BY model_name
            ORDER BY count DESC
        """)
        by_model = {row[0]: row[1] for row in cursor.fetchall()}

        # Date range
        cursor.execute("""
            SELECT MIN(timestamp) as first, MAX(timestamp) as last
            FROM model_chat
        """)
        date_range = cursor.fetchone()

        conn.close()

        return {
            "total_messages": total,
            "by_model": by_model,
            "first_message": date_range[0],
            "last_message": date_range[1],
            "database_path": str(self.db_path)
        }

    def _row_to_model_message(self, row: sqlite3.Row) -> ModelMessage:
        """
        Convert SQLite row to ModelMessage

        Args:
            row: SQLite row object

        Returns:
            ModelMessage instance
        """
        # Get raw content (should contain USER_PROMPT, CHAIN_OF_THOUGHT, TRADING_DECISIONS)
        raw_content = row['raw_content'] or ""

        # Extract sections from raw_content
        user_prompt = self._extract_section(raw_content, "USER_PROMPT")
        chain_of_thought = self._extract_section(raw_content, "CHAIN_OF_THOUGHT")
        trading_decisions_text = self._extract_section(raw_content, "TRADING_DECISIONS")

        # Fallback: if sections not found, use database fields
        if not user_prompt:
            user_prompt = f"Market data analysis at {row['timestamp']}"

        if not chain_of_thought:
            chain_of_thought = row['reasoning'] or raw_content or ""

        # Parse trading decisions from structured data first
        trading_decisions = []
        if row['positions']:
            try:
                positions_data = json.loads(row['positions'])
                if isinstance(positions_data, list):
                    for pos in positions_data:
                        if isinstance(pos, dict):
                            trading_decisions.append(TradingDecision(
                                symbol=pos.get('symbol', 'UNKNOWN'),
                                action=pos.get('side', 'HOLD'),
                                confidence=float(pos.get('confidence', row['confidence'] or 0.5)),
                                quantity=pos.get('size')
                            ))
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # If no structured positions, try parsing from TRADING_DECISIONS text
        if not trading_decisions and trading_decisions_text:
            trading_decisions = self._parse_trading_decisions_text(trading_decisions_text)

        # If still no decisions but we have action field, create single decision
        if not trading_decisions and row['action']:
            trading_decisions.append(TradingDecision(
                symbol='UNKNOWN',
                action=row['action'],
                confidence=float(row['confidence'] or 0.5)
            ))

        # Parse market data if available
        market_data = {}
        if row['market_data']:
            try:
                market_data = json.loads(row['market_data'])
            except json.JSONDecodeError:
                pass

        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(row['timestamp'])
        except (ValueError, TypeError):
            timestamp = datetime.now()

        # Parse scraped_at
        try:
            scraped_at = datetime.fromisoformat(row['scraped_at'])
        except (ValueError, TypeError):
            scraped_at = datetime.now()

        # Create ModelMessage
        return ModelMessage(
            model_name=row['model_name'],
            timestamp=timestamp,
            message_id=row['message_hash'],
            user_prompt=user_prompt,
            market_data=market_data,
            chain_of_thought=chain_of_thought,
            trading_decisions=trading_decisions,
            account_value=None,  # Not stored in extension DB
            total_return=None,
            sharpe_ratio=None,
            scraped_at=scraped_at
        )

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        Extract a section from formatted content

        Args:
            content: Full raw content
            section_name: Section to extract (USER_PROMPT, CHAIN_OF_THOUGHT, TRADING_DECISIONS)

        Returns:
            Extracted section content or empty string
        """
        import re

        # Try exact marker format first (e.g., "▶\nUSER_PROMPT\n")
        pattern = rf"▶\s*{section_name}\s*\n(.*?)(?=▶|$)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Try without arrow marker
        pattern = rf"{section_name}\s*\n(.*?)(?={section_name.split()[0]}|$)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        return ""

    def _parse_trading_decisions_text(self, text: str) -> List[TradingDecision]:
        """
        Parse trading decisions from text format

        Args:
            text: TRADING_DECISIONS section text

        Returns:
            List of TradingDecision objects
        """
        import re

        decisions = []

        # Pattern: Symbol\nAction\nConfidence%\nQUANTITY: value
        # Example:
        # ETH
        # HOLD
        # 75%
        # QUANTITY: -2.49

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        i = 0
        while i < len(lines):
            # Look for symbol (usually all caps, 2-5 letters)
            if re.match(r'^[A-Z]{2,5}$', lines[i]):
                symbol = lines[i]

                # Next should be action
                if i + 1 < len(lines):
                    action = lines[i + 1].upper()

                    # Next might be confidence
                    confidence = 0.5
                    quantity = None

                    if i + 2 < len(lines):
                        conf_match = re.match(r'(\d+)%', lines[i + 2])
                        if conf_match:
                            confidence = float(conf_match.group(1)) / 100.0

                            # Check for quantity
                            if i + 3 < len(lines):
                                qty_match = re.match(r'QUANTITY:\s*([-\d.]+)', lines[i + 3])
                                if qty_match:
                                    quantity = float(qty_match.group(1))
                                    i += 4
                                else:
                                    i += 3
                            else:
                                i += 3
                        else:
                            i += 2
                    else:
                        i += 2

                    decisions.append(TradingDecision(
                        symbol=symbol,
                        action=action,
                        confidence=confidence,
                        quantity=quantity
                    ))
                else:
                    i += 1
            else:
                i += 1

        return decisions
