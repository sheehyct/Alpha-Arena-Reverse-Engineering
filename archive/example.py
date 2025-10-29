"""
Example script showing how to use the nof1.ai scraper

This demonstrates the basic workflow for scraping and storing data.
Run this in Claude Code with MCP for full functionality.
"""

from pathlib import Path
from src.scraper import Nof1Scraper, ScrapeSession
from src.models import ModelMessage, TradingDecision
from datetime import datetime

def main():
    """Main example function"""

    print("=" * 70)
    print("NOF1.AI SCRAPER EXAMPLE")
    print("=" * 70)

    # Initialize the scraper
    scraper = Nof1Scraper(
        data_dir=Path("./data"),
        max_messages=10,
        filter_model=None,  # Set to "Claude Sonnet 4.5" to filter
        use_openmemory=True,
    )

    print("\n1. Scraper initialized successfully!")

    # Show the navigation guide
    print("\n2. Navigation Guide:")
    print("-" * 70)
    scraper.print_navigation_guide()

    # Get a scraping plan
    print("\n3. Getting scraping plan...")
    plan = scraper.get_scraping_plan()

    print(f"\nSteps to execute: {len(plan['steps'])}")
    print(f"Max messages: {plan['config']['max_messages']}")

    # Create a scrape session for tracking
    session = ScrapeSession(scraper)

    print("\n4. Example: Creating a mock message...")

    # Create an example message (normally this would come from browser snapshots)
    example_message = ModelMessage(
        model_name="Claude Sonnet 4.5",
        timestamp=datetime.now(),
        user_prompt="Market data showing BTC at $113,000...",
        chain_of_thought="""
        Let me analyze the current market conditions:

        1. BTC is trading at $113,000 with strong momentum
        2. The 4H MACD is positive at 28.095
        3. RSI is at 63, not yet overbought
        4. Volume is confirming the move

        Based on this analysis, I believe we should hold our current
        long position and wait for either:
        - Price to hit profit target at $115,000
        - MACD to turn negative
        - Price to close below $110,000 on 4H

        The risk/reward is favorable here with tight stop loss.
        """,
        trading_decisions=[
            TradingDecision(
                symbol="BTC",
                action="HOLD",
                confidence=0.75,
                quantity=0.5
            )
        ],
        account_value=10500.00,
        total_return=5.0,
        sharpe_ratio=0.45,
    )

    print("\n5. Storing example message...")

    # Store the message
    success = scraper.store_message(example_message)

    if success:
        print("[OK] Message stored successfully!")

        # Add to session
        session.add_message(example_message)

    # Get OpenMemory store data
    print("\n6. OpenMemory storage data:")
    om_data = scraper.get_openmemory_store_call(example_message)

    print(f"Content length: {len(om_data['content'])} characters")
    print(f"Tags: {om_data['tags']}")
    print(f"Metadata keys: {list(om_data['metadata'].keys())}")

    # Show storage stats
    print("\n7. Current storage statistics:")
    print("-" * 70)
    stats = scraper.get_storage_stats()

    print(f"Total messages: {stats['total_messages']}")
    print(f"Unique models: {stats['unique_models']}")
    print(f"Storage path: {stats['storage_path']}")

    # Generate summary
    print("\n8. Session summary:")
    print("-" * 70)
    session.print_result()

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("""
    To actually scrape nof1.ai, you need to:

    1. Open this workspace in Claude Code
    2. Ensure MCP servers are configured (.claude/mcp.json)
    3. Ask Claude Code to execute the scraping plan:

       "Navigate to nof1.ai and scrape the latest 20 messages"

    4. Claude Code will:
       - Use mcp__playwright__browser_navigate
       - Click through the UI
       - Extract chain of thought data
       - Store in local files and OpenMemory

    5. Query the data:
       "Query OpenMemory for risk management strategies"

    See CLAUDE_CODE_GUIDE.md for detailed instructions!
    """)


if __name__ == "__main__":
    main()
