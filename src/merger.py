"""
Data merger - combines Chrome Extension and Playwright data sources
Deduplicates by content hash and timestamp
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import json

from .models import ModelMessage
from .sqlite_reader import ExtensionDataReader
from .storage import StorageManager


class DataMerger:
    """Merges data from multiple sources with deduplication"""

    def __init__(self, extension_db_path: Path, playwright_data_dir: Path):
        """
        Initialize merger

        Args:
            extension_db_path: Path to Chrome extension SQLite database
            playwright_data_dir: Path to Playwright scraped data directory
        """
        self.extension_reader = ExtensionDataReader(extension_db_path)
        self.playwright_storage = StorageManager(playwright_data_dir)

    def merge_all(self, priority_source: str = "extension") -> List[ModelMessage]:
        """
        Merge all data from both sources

        Args:
            priority_source: Which source to prioritize on conflicts ("extension" or "playwright")

        Returns:
            List of deduplicated ModelMessage objects
        """
        print("Reading Chrome extension data...")
        extension_messages = self.extension_reader.read_all_messages()
        print(f"  Found {len(extension_messages)} extension messages")

        print("Reading Playwright scraped data...")
        playwright_messages = self.playwright_storage.load_all_messages()
        print(f"  Found {len(playwright_messages)} Playwright messages")

        print("Merging and deduplicating...")
        merged = self._deduplicate_messages(
            extension_messages,
            playwright_messages,
            priority_source
        )

        print(f"  Result: {len(merged)} unique messages")
        return merged

    def merge_by_model(
        self,
        model_name: str,
        priority_source: str = "extension"
    ) -> List[ModelMessage]:
        """
        Merge data for a specific model

        Args:
            model_name: Name of model to merge
            priority_source: Which source to prioritize on conflicts

        Returns:
            List of deduplicated ModelMessage objects for the specified model
        """
        extension_messages = self.extension_reader.read_all_messages(model_name)
        playwright_messages = [
            msg for msg in self.playwright_storage.load_all_messages()
            if msg.model_name.lower() == model_name.lower()
        ]

        return self._deduplicate_messages(
            extension_messages,
            playwright_messages,
            priority_source
        )

    def get_merge_statistics(self) -> Dict:
        """Get statistics about merged data"""
        extension_stats = self.extension_reader.get_statistics()

        # Get Playwright stats
        playwright_messages = self.playwright_storage.load_all_messages()
        playwright_by_model = defaultdict(int)
        for msg in playwright_messages:
            playwright_by_model[msg.model_name] += 1

        # Perform merge to get deduplicated count
        merged = self.merge_all()
        merged_by_model = defaultdict(int)
        for msg in merged:
            merged_by_model[msg.model_name] += 1

        return {
            "extension": extension_stats,
            "playwright": {
                "total_messages": len(playwright_messages),
                "by_model": dict(playwright_by_model)
            },
            "merged": {
                "total_unique_messages": len(merged),
                "by_model": dict(merged_by_model),
                "duplicates_removed": (
                    extension_stats["total_messages"] +
                    len(playwright_messages) -
                    len(merged)
                )
            }
        }

    def _deduplicate_messages(
        self,
        extension_messages: List[ModelMessage],
        playwright_messages: List[ModelMessage],
        priority_source: str
    ) -> List[ModelMessage]:
        """
        Deduplicate messages by content hash and timestamp

        Strategy:
        1. Create composite key from (model_name, content_hash, timestamp_rounded)
        2. If duplicate found, keep the one from priority_source
        3. Return sorted by timestamp (newest first)

        Args:
            extension_messages: Messages from Chrome extension
            playwright_messages: Messages from Playwright scraper
            priority_source: Which source wins on conflicts

        Returns:
            Deduplicated list of messages
        """
        seen_keys: Set[str] = set()
        unique_messages: Dict[str, Tuple[ModelMessage, str]] = {}

        # Process both sources
        sources = []
        if priority_source == "extension":
            sources = [
                (extension_messages, "extension"),
                (playwright_messages, "playwright")
            ]
        else:
            sources = [
                (playwright_messages, "playwright"),
                (extension_messages, "extension")
            ]

        for messages, source_name in sources:
            for msg in messages:
                # Create deduplication key
                key = self._create_dedup_key(msg)

                if key not in seen_keys:
                    # New message
                    seen_keys.add(key)
                    unique_messages[key] = (msg, source_name)
                else:
                    # Duplicate found - keep the one from priority source
                    existing_msg, existing_source = unique_messages[key]
                    if source_name == priority_source:
                        # Replace with priority source
                        unique_messages[key] = (msg, source_name)

        # Extract messages and sort by timestamp (newest first)
        result = [msg for msg, _ in unique_messages.values()]
        result.sort(key=lambda m: m.timestamp, reverse=True)

        return result

    def _create_dedup_key(self, msg: ModelMessage) -> str:
        """
        Create deduplication key for a message

        Uses: model_name + content_hash + timestamp_rounded_to_minute

        Args:
            msg: ModelMessage to create key for

        Returns:
            Deduplication key string
        """
        # Hash the chain of thought content
        content_hash = hashlib.sha256(
            msg.chain_of_thought.encode('utf-8')
        ).hexdigest()[:16]

        # Round timestamp to nearest minute (handles slight timing differences)
        timestamp_rounded = msg.timestamp.replace(second=0, microsecond=0)

        # Create composite key
        key = f"{msg.model_name}:{content_hash}:{timestamp_rounded.isoformat()}"
        return key

    def export_merged_to_json(
        self,
        output_path: Path,
        model_name: Optional[str] = None
    ):
        """
        Export merged data to JSON file

        Args:
            output_path: Where to save JSON file
            model_name: Optional filter for specific model
        """
        if model_name:
            merged = self.merge_by_model(model_name)
        else:
            merged = self.merge_all()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-serializable format
        data = [json.loads(msg.model_dump_json()) for msg in merged]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Exported {len(data)} messages to {output_path}")
