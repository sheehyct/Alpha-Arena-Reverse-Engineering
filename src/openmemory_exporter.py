"""
OpenMemory exporter - prepares data for OpenMemory MCP storage
Claude Code will call the actual MCP tools
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import ModelMessage
from .merger import DataMerger


class OpenMemoryExporter:
    """
    Prepares ModelMessage data for export to OpenMemory

    This class prepares the data, but Claude Code (you!) will actually
    call the MCP tools: mcp__openmemory__openmemory_store
    """

    def __init__(self, merger: DataMerger):
        """
        Initialize exporter

        Args:
            merger: DataMerger instance with access to both data sources
        """
        self.merger = merger

    def prepare_all_for_export(
        self,
        model_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare all merged messages for OpenMemory export

        Args:
            model_filter: Optional filter for specific model (e.g., "deepseek-v3.1")

        Returns:
            List of dicts with {content, tags, metadata} ready for MCP storage
        """
        if model_filter:
            messages = self.merger.merge_by_model(model_filter)
        else:
            messages = self.merger.merge_all()

        prepared = []
        for msg in messages:
            prepared.append(self.prepare_message(msg))

        return prepared

    def prepare_message(self, msg: ModelMessage) -> Dict[str, Any]:
        """
        Prepare a single message for OpenMemory storage

        Returns dict with fields that match mcp__openmemory__openmemory_store parameters:
        - content: Formatted reasoning text
        - tags: List of tags for categorization
        - metadata: Additional structured data

        Args:
            msg: ModelMessage to prepare

        Returns:
            Dict ready for MCP tool call
        """
        # Format content for semantic search
        content = self._format_content(msg)

        # Generate tags for categorization
        tags = self._generate_tags(msg)

        # Create metadata
        metadata = self._generate_metadata(msg)

        return {
            "content": content,
            "tags": tags,
            "metadata": metadata
        }

    def _format_content(self, msg: ModelMessage) -> str:
        """
        Format message content for OpenMemory semantic search

        This is what will be semantically indexed and searched
        """
        lines = []
        lines.append(f"=== {msg.model_name} Trading Analysis ===")
        lines.append(f"Time: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Add performance metrics if available
        if msg.account_value or msg.total_return or msg.sharpe_ratio:
            lines.append("Performance Metrics:")
            if msg.account_value:
                lines.append(f"  Account Value: ${msg.account_value:,.2f}")
            if msg.total_return:
                lines.append(f"  Total Return: {msg.total_return:+.2f}%")
            if msg.sharpe_ratio:
                lines.append(f"  Sharpe Ratio: {msg.sharpe_ratio:.2f}")
            lines.append("")

        # Main chain of thought reasoning
        lines.append("Chain of Thought Reasoning:")
        lines.append(msg.chain_of_thought)
        lines.append("")

        # Trading decisions
        if msg.trading_decisions:
            lines.append("Trading Decisions:")
            for decision in msg.trading_decisions:
                lines.append(
                    f"  • {decision.symbol}: {decision.action} "
                    f"(Confidence: {decision.confidence:.1%})"
                )
                if decision.quantity:
                    lines.append(f"    Quantity: {decision.quantity}")
            lines.append("")

        return "\n".join(lines)

    def _generate_tags(self, msg: ModelMessage) -> List[str]:
        """
        Generate tags for OpenMemory categorization

        Tags help with filtering and organization
        """
        tags = []

        # Model name (normalized)
        model_tag = msg.model_name.lower().replace(" ", "_")
        tags.append(f"model_{model_tag}")

        # Priority models get special tags
        if "deepseek" in model_tag:
            tags.append("priority_1_highest_pl")
        elif "qwen" in model_tag:
            tags.append("priority_2_second_pl")
        elif "claude" in model_tag:
            tags.append("priority_3_negative_pl")

        # Date tags
        tags.append(f"date_{msg.timestamp.strftime('%Y_%m_%d')}")
        tags.append(f"year_{msg.timestamp.year}")
        tags.append(f"month_{msg.timestamp.strftime('%Y_%m')}")

        # Symbol tags
        for decision in msg.trading_decisions:
            tags.append(f"symbol_{decision.symbol.lower()}")
            tags.append(f"action_{decision.action.lower()}")

        # Confidence level tags
        for decision in msg.trading_decisions:
            if decision.confidence >= 0.8:
                tags.append("high_confidence")
            elif decision.confidence >= 0.5:
                tags.append("medium_confidence")
            else:
                tags.append("low_confidence")

        # Performance tags
        if msg.total_return:
            if msg.total_return > 0:
                tags.append("profitable")
            else:
                tags.append("unprofitable")

        return list(set(tags))  # Remove duplicates

    def _generate_metadata(self, msg: ModelMessage) -> Dict[str, Any]:
        """
        Generate metadata for OpenMemory

        Metadata is structured data that accompanies the content
        """
        metadata = {
            "model_name": msg.model_name,
            "timestamp": msg.timestamp.isoformat(),
            "message_id": msg.message_id,
            "scraped_at": msg.scraped_at.isoformat(),
        }

        # Add performance metrics
        if msg.account_value is not None:
            metadata["account_value"] = msg.account_value
        if msg.total_return is not None:
            metadata["total_return"] = msg.total_return
        if msg.sharpe_ratio is not None:
            metadata["sharpe_ratio"] = msg.sharpe_ratio

        # Add trading decisions summary
        if msg.trading_decisions:
            metadata["symbols"] = [d.symbol for d in msg.trading_decisions]
            metadata["actions"] = [d.action for d in msg.trading_decisions]
            metadata["avg_confidence"] = sum(
                d.confidence for d in msg.trading_decisions
            ) / len(msg.trading_decisions)

        return metadata

    def get_export_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about what will be exported

        Returns:
            Dict with export statistics
        """
        all_prepared = self.prepare_all_for_export()

        # Count by model
        by_model = {}
        for item in all_prepared:
            model = item["metadata"]["model_name"]
            by_model[model] = by_model.get(model, 0) + 1

        # Tag statistics
        all_tags = []
        for item in all_prepared:
            all_tags.extend(item["tags"])

        from collections import Counter
        tag_counts = Counter(all_tags)

        return {
            "total_messages": len(all_prepared),
            "by_model": by_model,
            "unique_tags": len(set(all_tags)),
            "top_tags": dict(tag_counts.most_common(20))
        }

    def export_sample_to_file(self, output_path: Path, limit: int = 5):
        """
        Export sample prepared data to JSON file for inspection

        Args:
            output_path: Where to save the sample
            limit: Number of samples to export
        """
        import json

        prepared = self.prepare_all_for_export()[:limit]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(prepared, f, indent=2, ensure_ascii=False)

        print(f"Exported {len(prepared)} sample messages to {output_path}")
        print("Review this before sending to OpenMemory")
