# Session Start Instructions

## Context Restoration

You are continuing work on the DeepSeek Analysis project - a quantitative analysis of AI trading strategies from the nof1.ai competition.

### First Actions on Session Start

1. Read claude.md for professional standards
2. Query OpenMemory for project context: `mcp__openmemory__openmemory_query` with query "DeepSeek Analysis project"
3. Review PROJECT_TREE.md for current structure (if exists)
4. Check git status to understand current state

### Project Overview

Analyzing trading strategies from AI models in crypto derivatives competition (Oct 17 - Nov 1, 2025).

Database: collector/nof1_data.db
- 4,425 total messages captured
- 3,543 structured reasoning records extracted
- 7 models analyzed

Main framework: workflows/comprehensive_analysis.py
- Consolidated analysis system with 6 modular phases
- Production-ready, institutional-grade code

### Data Coverage

Coverage: Oct 29-31 (correction phase only)
- Bull phase (Oct 17-27): Not captured (project started after)
- Correction phase (Oct 29-31): Complete data
- Can infer strategy behavior from reasoning chains

### Key Findings Already Validated

1. Inverse confidence-indicator relationship (66% validation rate)
   - High confidence = fewer, simpler indicators
   - Quality over quantity principle confirmed

2. Model divergence in exit philosophy
   - claude-sonnet-4-5: 85% invalidation (rule-following)
   - qwen3-max: 6% invalidation (profit-chasing)

3. Risk scales with confidence
   - High confidence: 7.2% risk
   - Medium confidence: 4.2% risk

4. All models mention stop losses 100% of time

### Current Analysis Status

Comprehensive framework complete and tested.
OpenMemory populated with critical findings.
Ready for ongoing analysis with available data.

Next competition: Will deploy real-time scraping from day 1.

### Working Principles

From claude.md:
- No emojis or special characters in code/docs
- Accuracy over speed always
- Unbiased, evidence-based analysis
- Institutional-grade engineering standards
- Maintain clean workspace organization
- Update PROJECT_TREE.md when structure changes

### Common Commands

Run complete analysis:
```bash
uv run python workflows/comprehensive_analysis.py --all
```

Run specific phase:
```bash
uv run python workflows/comprehensive_analysis.py --phase [stats|diagnostic|costs|regime|claude-self|meta]
```

Extract portfolio data:
```bash
uv run python workflows/extract_portfolio_data.py
```

### OpenMemory Usage

Critical knowledge stored in OpenMemory sectors:
- reflective: Project decisions and self-analysis
- semantic: Key findings and statistics
- procedural: Workflows and technical processes

Query for specific topics:
```
mcp__openmemory__openmemory_query with query "[topic]"
```

Store new insights:
```
mcp__openmemory__openmemory_store with content "[insight]"
```

### Project Philosophy

This is production-quality quantitative finance research.
Treat all code as if it will trade real capital and be reviewed by institutional risk committees.
Apply professional software engineering and quantitative finance domain expertise.

### If User Says "Continue where we left off"

1. Query OpenMemory for latest context
2. Check git status and recent commits
3. Review any uncommitted changes
4. Ask user what specific aspect they want to continue with
5. Reference relevant findings from memory

### If Context is Lost

OpenMemory contains all critical findings and decisions.
Query with broad terms like "project", "findings", "analysis", "models" to restore context.

## Planned Workflow (No Additional API Costs)

### Phase 1: Preliminary Analysis (Next Session - FREE)
User has already spent $60 on batch extraction. NO additional API costs needed.

Run complete analysis with existing data:
```bash
uv run python workflows/comprehensive_analysis.py --all
```

Focus areas:
1. Correction phase performance (Oct 29-31) - which models protected capital?
2. Strategy inference from 3,543 reasoning chains
3. Model comparison: What did Gemini (+20.17%) do differently?
4. Document invalidation levels, risk patterns, indicator combinations
5. Generate preliminary insights

### Phase 2: Final Results Integration (Nov 3rd - FREE)
1. Collect final competition results from nof1.ai website (public, free)
2. Update analysis with complete returns including bull phase
3. Validate hypotheses about regime-dependent performance
4. Generate final conclusions

### Phase 3: Additional Extraction (ONLY IF CRITICAL GAPS - PAID)
Only extract more data if reasoning chains prove insufficient.
Assessment: Likely NOT needed - have complete strategy DNA in 3,543 records.

## Ready to Continue

You are now equipped to seamlessly continue the project with full context restoration capabilities.
