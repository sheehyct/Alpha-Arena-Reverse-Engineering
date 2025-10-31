# Extraction Strategy - Final Plan

## The Situation

**Total Messages:** 4,425
**Your Budget:** $50 (need to add $14 for $64 total)
**Cost:** $63.77 for 3,543 substantive messages

## What We Discovered

### unknown-model is NOT "hold Bitcoin"!

**Analysis reveals:**
- 37.4% empty (871 messages) - No reasoning, skip
- 62.6% substantive (1,456 messages) - Real trading analysis
- 62% mention MACD, RSI, entry, exit signals
- **These are real model decisions with failed model_id extraction**

### Message Breakdown by Model

```
deepseek-chat-v3.1  :  278 messages | Avg: 19,902 chars (longest reasoning)
gpt-5               :  287 messages | Avg: 16,430 chars
gemini-2.5-pro      :  374 messages | Avg: 15,522 chars
claude-sonnet-4-5   :  364 messages | Avg: 13,067 chars
grok-4              :  311 messages | Avg: 13,133 chars
qwen3-max           :  484 messages | Avg:  9,574 chars
unknown-model       : 2,327 messages | Avg:  5,563 chars (when non-empty)
```

## The Strategy: Two-Track Extraction

### Track 1: Extract All Substantive Messages
**Cost: $63.77** (3,543 messages)

**Command:**
```powershell
uv run python workflows/extract_structured_reasoning.py
```

**What it does:**
- Automatically skips empty/tiny (<500 chars) messages
- Processes all 6 known models + substantive unknown-model
- Extracts: entry indicators, exit reasons, stop loss rationale, WHY reasoning
- Creates structured_reasoning table in SQLite

### Track 2: Identify Unknown Models
**After extraction, run identification:**

```powershell
uv run python workflows/identify_unknown_models.py
```

**What it does:**
1. Builds fingerprints from known models (reasoning length, indicator patterns, style)
2. Compares unknown-model messages against fingerprints
3. Assigns likely source model with confidence score
4. Updates database with identifications

**Matching criteria:**
- Reasoning length similarity (30% weight)
- Entry indicator overlap (25% weight)
- Exit type patterns (15% weight)
- Confidence expression style (15% weight)
- Risk management keywords (15% weight)

## Why This Strategy Works

### Problem: Can't Analyze Without Model Attribution
Without knowing which model made the decision, we can't:
- Compare reasoning quality across models
- Identify model-specific patterns
- Build model-specific trading strategies

### Solution: Pattern Matching Re-Attribution
The unknown-model messages likely came from one of the 6 models due to:
- Timing issues during capture
- Failed JSON parsing
- Missing model_id field

By matching reasoning patterns, we can recover ~60-70% of these attributions.

## Cost Justification

**Alternative Strategy: Skip all unknown-model**
- Cost: $37.76 for 2,098 messages
- Saves: $26.01
- Loses: 1,456 substantive trading decisions (~41% of data!)

**Our Strategy: Extract everything substantive**
- Cost: $63.77 for 3,543 messages
- Additional: $14 to credits
- Gains: Complete dataset + ability to re-attribute unknowns

**ROI:** Recovering 1,456 additional trading decisions is worth $26 extra.

## Implementation Steps

### Step 1: Add Credits
Add $14 to your Anthropic account for $64 total.

### Step 2: Set API Key
```powershell
$env:ANTHROPIC_API_KEY='your-key'
```

### Step 3: Verify Cost
```powershell
uv run python workflows/extract_structured_reasoning.py --dry-run
```

Expected output:
```
Messages to process: 3,543
Standard API cost: $63.77
```

### Step 4: Extract
```powershell
uv run python workflows/extract_structured_reasoning.py
```

This will:
- Process each message through Claude API
- Extract structured reasoning fields
- Save to structured_reasoning table
- Take ~1-2 hours (rate limits)

### Step 5: Identify Unknowns
```powershell
uv run python workflows/identify_unknown_models.py --confidence-threshold 0.6
```

Expected results:
- ~60-70% of unknown-model identified
- Confidence scores for each match
- Updated model attributions

### Step 6: Update Database (optional)
```powershell
uv run python workflows/identify_unknown_models.py --update-database
```

This re-attributes identified messages to their likely source models.

## Analysis After Extraction

### Query Examples

**Risk management by model:**
```sql
SELECT
    model_name,
    stop_loss_rationale,
    COUNT(*)
FROM structured_reasoning
WHERE stop_loss_placement IS NOT NULL
GROUP BY model_name, stop_loss_rationale
```

**Exit patterns:**
```sql
SELECT
    model_name,
    exit_type,
    COUNT(*),
    AVG(LENGTH(exit_reason)) as avg_reasoning_length
FROM structured_reasoning
GROUP BY model_name, exit_type
ORDER BY COUNT(*) DESC
```

**High confidence trades:**
```sql
SELECT
    model_name,
    decision_summary,
    confidence_reasoning
FROM structured_reasoning
WHERE confidence_level = 'high'
ORDER BY model_name
```

## What You Get

### Structured Fields Per Message
- Entry indicators used
- Entry conditions and rationale
- Exit trigger and reason
- Stop loss placement and why
- Risk management approach
- Market conditions assessed
- Confidence level and reasoning
- Causal reasoning chain
- One-sentence summary

### Analytics Capabilities
- "Show all DeepSeek trades with MACD+RSI entry and profit target exit"
- "Compare stop loss placement rationale across priority models"
- "What confidence patterns correlate with trade success?"
- "How do models adapt to volatile vs trending markets?"
- "Which indicators co-occur most frequently?"

## Final Notes

### Why Not Just Priority Models?
Priority models only (DeepSeek, QWEN3, Claude) = 1,126 messages for $20.27

But you'd miss:
- Gemini's unique short bias patterns
- GPT-5's longest reasoning chains
- Grok-4's approaches
- 1,456 unattributed decisions

For $43 more, you get 2.5x more data + complete model comparison.

### One Shot Only
You can't re-extract messages without paying again. This is your one chance to get complete structured data.

**Recommendation:** Go all-in. Extract everything substantive. Identify unknowns. Get the full picture.
