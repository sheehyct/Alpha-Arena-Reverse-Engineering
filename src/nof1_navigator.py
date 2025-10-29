"""
Navigator for nof1.ai using Playwright MCP server

This module provides instructions and data structures for navigating nof1.ai
when running through Claude Code with MCP Playwright integration.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from rich.console import Console

console = Console()


@dataclass
class NavigationConfig:
    """Configuration for nof1.ai navigation"""
    url: str = "https://nof1.ai/"
    max_messages: int = 50
    filter_model: Optional[str] = None
    scroll_wait_ms: int = 2000


class Nof1Navigator:
    """
    Handles navigation logic for nof1.ai

    Note: This class contains the logic and instructions, but actual browser
    automation happens through MCP Playwright tools when running in Claude Code.
    """

    def __init__(self, config: NavigationConfig):
        self.config = config

    def get_navigation_steps(self) -> List[str]:
        """
        Get step-by-step navigation instructions for Claude Code

        Returns:
            List of navigation steps as instructions
        """
        steps = [
            f"1. Navigate to {self.config.url}",
            "2. Wait for page to load completely",
            "3. Click the MODELCHAT button to switch to the chat view",
            "4. Wait for messages to load",
        ]

        if self.config.filter_model:
            steps.extend([
                "5. Click the 'ALL MODELS ▼' dropdown",
                f"6. Select '{self.config.filter_model}' from the dropdown",
                "7. Wait for filtered messages to load",
            ])

        steps.extend([
            "8. Get browser snapshot to identify message elements",
            "9. For each message element (up to max_messages):",
            "   a. Click the message to expand it",
            "   b. Wait for expansion animation",
            "   c. Take snapshot of expanded message",
            "   d. Extract data from snapshot",
            "   e. Click again to collapse (optional)",
            "10. Scroll down if more messages needed",
            "11. Repeat step 9 for new messages",
        ])

        return steps

    def get_selector_patterns(self) -> Dict[str, str]:
        """
        Get CSS selectors and patterns for nof1.ai elements

        These are used when running browser automation
        """
        return {
            "modelchat_button": "button:has-text('MODELCHAT')",
            "model_filter_dropdown": "button:has-text('ALL MODELS')",
            "message_container": ".group.cursor-pointer",
            "message_header": "heading[level=3]",
            "expand_button": "button[contains text 'USER_PROMPT' or 'CHAIN']",
            "user_prompt_section": "button:has-text('USER_PROMPT')",
            "chain_of_thought_section": "button:has-text('CHAIN_OF_THOUGHT')",
            "trading_decisions_section": "button:has-text('TRADING_DECISIONS')",
        }

    def extract_message_list_from_snapshot(self, snapshot: str) -> List[Dict[str, Any]]:
        """
        Extract list of messages from page snapshot

        Args:
            snapshot: YAML-formatted page snapshot from Playwright

        Returns:
            List of message metadata (model name, timestamp, ref)
        """
        messages = []

        # Parse the snapshot to find message elements
        # This is a simplified version - actual parsing would be more robust
        import re

        # Look for patterns like:
        # - img "Claude Sonnet 4.5" [ref=eXXX]
        # - generic [ref=eXXX]: CLAUDE SONNET 4.5
        # - generic [ref=eXXX]: 10/29 07:57:57

        # Extract message blocks
        message_pattern = r'img "([^"]+)" \[ref=(e\d+)\].*?(\d{1,2}/\d{1,2} \d{2}:\d{2}:\d{2})'

        for match in re.finditer(message_pattern, snapshot, re.DOTALL):
            model_name, ref, timestamp = match.groups()

            messages.append({
                "model_name": model_name,
                "timestamp": timestamp,
                "ref": ref,
                "element_locator": f"[ref={ref}]",
            })

        console.print(f"[dim]Extracted {len(messages)} messages from snapshot[/dim]")
        return messages

    def get_mcp_navigation_plan(self) -> Dict[str, Any]:
        """
        Generate a plan for MCP Playwright tools

        This returns a structured plan that can be executed via MCP
        """
        return {
            "steps": [
                {
                    "action": "navigate",
                    "tool": "mcp__playwright__browser_navigate",
                    "params": {"url": self.config.url},
                },
                {
                    "action": "click_modelchat",
                    "tool": "mcp__playwright__browser_click",
                    "params": {
                        "element": "MODELCHAT button",
                        "selector": "button:has-text('MODELCHAT')",
                    },
                },
                {
                    "action": "wait",
                    "duration_ms": 1000,
                },
                {
                    "action": "snapshot",
                    "tool": "mcp__playwright__browser_snapshot",
                    "params": {},
                },
            ],
            "config": {
                "max_messages": self.config.max_messages,
                "filter_model": self.config.filter_model,
                "scroll_wait_ms": self.config.scroll_wait_ms,
            },
        }


class MessageExpander:
    """Handles expanding and extracting individual messages"""

    @staticmethod
    def expand_message(message_ref: str) -> Dict[str, Any]:
        """
        Generate instructions for expanding a specific message

        Args:
            message_ref: The element reference (e.g., "e975")

        Returns:
            Dictionary with expansion instructions
        """
        return {
            "action": "expand_message",
            "tool": "mcp__playwright__browser_click",
            "params": {
                "element": f"Message with ref {message_ref}",
                "ref": message_ref,
            },
        }

    @staticmethod
    def extract_expanded_message(snapshot: str) -> Dict[str, Any]:
        """
        Extract data from an expanded message snapshot

        Args:
            snapshot: YAML snapshot of the expanded message

        Returns:
            Dictionary with extracted sections
        """
        # Parse the snapshot to extract the three main sections
        import re

        sections = {}

        # Extract USER_PROMPT section
        user_prompt_pattern = r"USER_PROMPT.*?(?=CHAIN_OF_THOUGHT|$)"
        user_match = re.search(user_prompt_pattern, snapshot, re.DOTALL)
        if user_match:
            sections["user_prompt"] = user_match.group(0)

        # Extract CHAIN_OF_THOUGHT section
        cot_pattern = r"CHAIN_OF_THOUGHT.*?(?=TRADING_DECISIONS|$)"
        cot_match = re.search(cot_pattern, snapshot, re.DOTALL)
        if cot_match:
            sections["chain_of_thought"] = cot_match.group(0)

        # Extract TRADING_DECISIONS section
        decisions_pattern = r"TRADING_DECISIONS.*?(?=generic \[ref=|$)"
        decisions_match = re.search(decisions_pattern, snapshot, re.DOTALL)
        if decisions_match:
            sections["trading_decisions"] = decisions_match.group(0)

        return sections


# Usage instructions for Claude Code environment:
"""
When running this scraper in Claude Code with MCP, the workflow is:

1. Initialize navigator:
   navigator = Nof1Navigator(NavigationConfig(max_messages=20))

2. Get the navigation plan:
   plan = navigator.get_mcp_navigation_plan()

3. Execute each step using MCP tools:
   - Use mcp__playwright__browser_navigate(url=config.url)
   - Use mcp__playwright__browser_click(element="MODELCHAT button", ref=...)
   - Use mcp__playwright__browser_snapshot() to get page state
   - Parse snapshot to find message elements
   - For each message:
     * Click to expand using mcp__playwright__browser_click
     * Take snapshot
     * Extract data using ChainExtractor
     * Store using StorageManager

4. The scraper module (scraper.py) will orchestrate this flow
"""
