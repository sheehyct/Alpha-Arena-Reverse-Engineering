"""Storage module for persisting scraped data"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from rich.console import Console

from .models import ModelMessage

console = Console()


class StorageManager:
    """Manages storage of scraped messages to both local files and OpenMemory"""

    def __init__(self, data_dir: Path, use_openmemory: bool = True):
        self.data_dir = data_dir
        self.raw_dir = data_dir / "raw"
        self.processed_dir = data_dir / "processed"
        self.use_openmemory = use_openmemory

        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def save_message(self, message: ModelMessage) -> bool:
        """
        Save a message to local storage and OpenMemory

        Args:
            message: The ModelMessage to save

        Returns:
            bool: True if saved successfully
        """
        try:
            # Save to local JSON
            self._save_to_json(message)

            # Save to OpenMemory if enabled
            if self.use_openmemory:
                self._save_to_openmemory(message)

            return True
        except Exception as e:
            console.print(f"[red]Error saving message: {e}[/red]")
            return False

    def _save_to_json(self, message: ModelMessage):
        """Save message to local JSON file"""
        # Create filename with timestamp and model name
        timestamp_str = message.timestamp.strftime("%Y%m%d_%H%M%S")
        model_slug = message.model_name.lower().replace(" ", "_")
        filename = f"{timestamp_str}_{model_slug}_{message.message_id[:8]}.json"

        filepath = self.raw_dir / filename

        # Save with pretty formatting
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                message.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
            )

        console.print(f"[dim]Saved to {filepath.name}[/dim]")

    def _save_to_openmemory(self, message: ModelMessage):
        """
        Save message to OpenMemory via MCP

        Note: This will be called via the MCP tools when the scraper runs
        through Claude Code. For standalone execution, this would use
        the OpenMemory API directly.
        """
        # Prepare content for OpenMemory
        content = message.to_openmemory_content()
        tags = message.to_tags()
        metadata = message.to_metadata()

        # In a Claude Code environment with MCP, this would trigger:
        # mcp__openmemory__openmemory_store(
        #     content=content,
        #     tags=tags,
        #     metadata=metadata
        # )

        console.print(
            f"[dim]Prepared for OpenMemory: {len(content)} chars, "
            f"{len(tags)} tags[/dim]"
        )

    def get_openmemory_store_data(self, message: ModelMessage) -> dict:
        """
        Get the data needed to store in OpenMemory
        This can be used by the CLI to call the MCP tool
        """
        return {
            "content": message.to_openmemory_content(),
            "tags": message.to_tags(),
            "metadata": message.to_metadata(),
        }

    def load_messages(
        self,
        model_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ModelMessage]:
        """
        Load messages from local storage with optional filtering

        Args:
            model_name: Filter by model name
            start_date: Filter messages after this date
            end_date: Filter messages before this date

        Returns:
            List of ModelMessage objects
        """
        messages = []

        # Iterate through JSON files
        for filepath in self.raw_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    message = ModelMessage(**data)

                    # Apply filters
                    if model_name and message.model_name != model_name:
                        continue

                    if start_date and message.timestamp < start_date:
                        continue

                    if end_date and message.timestamp > end_date:
                        continue

                    messages.append(message)

            except Exception as e:
                console.print(f"[yellow]Error loading {filepath.name}: {e}[/yellow]")

        return sorted(messages, key=lambda m: m.timestamp)

    def load_all_messages(self) -> List[ModelMessage]:
        """
        Load all messages from local storage (convenience method)

        Returns:
            List of all ModelMessage objects
        """
        return self.load_messages()

    def get_storage_stats(self) -> dict:
        """Get statistics about stored messages"""
        json_files = list(self.raw_dir.glob("*.json"))

        # Load all messages for stats
        messages = self.load_messages()

        models = set(m.model_name for m in messages)

        return {
            "total_messages": len(messages),
            "total_files": len(json_files),
            "unique_models": len(models),
            "models": sorted(models),
            "date_range": {
                "earliest": min(m.timestamp for m in messages) if messages else None,
                "latest": max(m.timestamp for m in messages) if messages else None,
            },
            "storage_path": str(self.raw_dir),
        }
