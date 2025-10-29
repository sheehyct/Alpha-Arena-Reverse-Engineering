# Workflow Automation Scripts

Professional, modular workflow scripts for DeepSeek trading analysis.

---

## Philosophy

These scripts follow professional software engineering principles:

### 1. Separation of Concerns
Each script has a single, well-defined responsibility:
- **start_capture.py**: Monitor data capture only
- **sync_to_openmemory.py**: Data preparation and export only
- **analyze_strategies.py**: Query generation and analysis only

### 2. Composability
Scripts are designed to work independently or together:
```bash
# Run individually
uv run python workflows/start_capture.py

# Chain together
uv run python workflows/sync_to_openmemory.py -y && \
uv run python workflows/analyze_strategies.py -q 5
```

### 3. Idempotency
Safe to run multiple times without side effects:
- Deduplication prevents duplicate storage
- Re-exports don't corrupt data
- Can recover from failures by re-running

### 4. Observability
Clear feedback at every step:
- Real-time progress indicators
- Live statistics
- Error messages with context
- Success confirmations

### 5. Fail-Fast
Clear error messages with actionable solutions:
```
Error: Extension database not found

Start the collector first:
  cd GPT_Implementation_Proposal/collector
  node server.js
```

---

## Scripts Overview

### start_capture.py

**Purpose:** Real-time monitoring of data capture

**Features:**
- Auto-detects if collector is running
- Shows startup instructions if needed
- Live statistics dashboard
- Updates every 5 seconds
- Graceful shutdown (Ctrl+C)

**Usage:**
```bash
uv run python workflows/start_capture.py
```

**Keep running:** Yes (monitors continuously)

---

### sync_to_openmemory.py

**Purpose:** Prepare and export data for OpenMemory

**Features:**
- Merges Extension + Playwright data
- Deduplication by content hash
- Model filtering support
- Progress bars
- Batch file generation
- Clear next-step instructions

**Usage:**
```bash
# All models
uv run python workflows/sync_to_openmemory.py

# Specific model
uv run python workflows/sync_to_openmemory.py --model "deepseek-v3.1"

# Skip confirmation
uv run python workflows/sync_to_openmemory.py -m "deepseek-v3.1" -y
```

**Run:** Periodically (every 2-4 hours)

---

### analyze_strategies.py

**Purpose:** Interactive query builder and analyzer

**Features:**
- 10 pre-defined queries
- Interactive menu system
- Custom query builder
- Model comparison tools
- MCP command generation
- Built-in help system

**Usage:**
```bash
# Interactive mode
uv run python workflows/analyze_strategies.py

# List queries
uv run python workflows/analyze_strategies.py --list

# Specific query
uv run python workflows/analyze_strategies.py --query 5
```

**Run:** As needed for analysis

---

## Design Decisions

### Why Not One Big Script?

**Problem with monolithic approach:**
- Capture runs continuously
- Sync runs periodically
- Analysis is interactive
- Different failure modes
- Hard to debug
- Tight coupling

**Benefits of modular approach:**
- Each script does one thing well
- Easy to understand and maintain
- Can run independently
- Clear boundaries
- Simple error handling
- Testable in isolation

---

### Why Not Background Services?

**Could have created:**
- Windows Services
- systemd units
- Supervisor configs

**But chose scripts because:**
- Simpler to understand
- Easier to debug
- More portable
- User has control
- Clear visibility
- No installation required

---

### Error Handling Strategy

**Fail-Fast with Context:**
```python
if not database.exists():
    console.print("[red]Error: Database not found[/red]")
    console.print("\nStart collector first:")
    console.print("  cd GPT_Implementation_Proposal/collector")
    console.print("  node server.js")
    sys.exit(1)
```

**Benefits:**
- Clear what went wrong
- Actionable solution provided
- No silent failures
- User knows exactly what to do

---

### Progress Feedback

**Real-time updates:**
- Live statistics (start_capture.py)
- Progress bars (sync_to_openmemory.py)
- Status messages at every step

**Benefits:**
- User knows system is working
- Can estimate completion time
- Can identify bottlenecks
- Builds trust in automation

---

## Terminal Organization

### Recommended Setup

**Terminal 1: Monitor (Always Running)**
```bash
uv run python workflows/start_capture.py
```
Purpose: Watch data collection in real-time

**Terminal 2: Services (Always Running)**
```bash
cd C:\Dev\openmemory\backend
npm run mcp
```
Purpose: OpenMemory MCP backend

**Terminal 3: Operations (Run as Needed)**
```bash
# Sync
uv run python workflows/sync_to_openmemory.py -m "deepseek-v3.1" -y

# Analyze
uv run python workflows/analyze_strategies.py
```
Purpose: Periodic operations and analysis

---

## Extension Points

### Adding New Workflows

Follow the same pattern:

1. **Single Responsibility**
   - One clear purpose
   - Well-defined input/output

2. **Error Handling**
   - Check prerequisites
   - Fail-fast with context
   - Actionable error messages

3. **Observability**
   - Progress indicators
   - Status messages
   - Clear output

4. **Documentation**
   - Docstrings
   - --help text
   - README entry

**Example:**
```python
class NewWorkflow:
    """Handles X operation

    Professional Principles:
    - Single responsibility (X only)
    - Fail-fast with clear errors
    - Observable (progress tracking)
    """

    def check_prerequisites(self) -> bool:
        """Check if required components available"""
        # Implementation

    def run(self):
        """Main workflow"""
        # Implementation
```

---

## Testing Workflows

### Manual Testing Checklist

**start_capture.py:**
- [ ] Detects running collector
- [ ] Shows instructions when collector not running
- [ ] Updates statistics every 5 seconds
- [ ] Handles Ctrl+C gracefully
- [ ] Shows final count on exit

**sync_to_openmemory.py:**
- [ ] Checks database exists
- [ ] Shows data summary
- [ ] Creates batch file
- [ ] Confirmation prompt works
- [ ] --yes flag skips prompt
- [ ] --model filters correctly

**analyze_strategies.py:**
- [ ] Interactive menu works
- [ ] All 10 queries display
- [ ] Custom query builder works
- [ ] Model comparison works
- [ ] Help system displays

---

## Dependencies

All workflows require:
- Python 3.12+
- UV package manager
- Rich library (for terminal UI)

Install:
```bash
uv add rich
```

---

## Troubleshooting

### Import Error: rich not found

**Solution:**
```bash
uv add rich
```

### Script won't run

**Check Python path:**
```bash
which python
# Should show UV's Python

uv run python --version
# Should show 3.12+
```

### Permission denied

**Windows:**
```bash
# Run as administrator if needed
```

**Unix:**
```bash
chmod +x workflows/*.py
```

---

## Performance Considerations

### start_capture.py
- Updates every 5 seconds (configurable)
- Minimal database queries
- Light on CPU

### sync_to_openmemory.py
- Progress bars for long operations
- Batch processing for efficiency
- Memory-efficient streaming

### analyze_strategies.py
- Interactive, no background processing
- Generates commands, doesn't execute them
- Zero MCP overhead

---

## Future Enhancements

Possible additions while maintaining principles:

1. **Automated Scheduling**
   - Wrapper script for cron/Task Scheduler
   - Still uses modular scripts underneath

2. **Email Notifications**
   - Alert on errors or milestones
   - Separate notification script

3. **Web Dashboard**
   - Read-only view of statistics
   - Doesn't replace CLI scripts

4. **Backup Workflow**
   - Export to additional formats
   - Follows same modular pattern

---

## Quick Reference

```bash
# Monitor capture
uv run python workflows/start_capture.py

# Export to OpenMemory
uv run python workflows/sync_to_openmemory.py -m "deepseek-v3.1" -y

# Analyze strategies
uv run python workflows/analyze_strategies.py -q 5
```

---

**See Also:**
- ../WORKFLOW_QUICKSTART.md - Usage guide
- ../INTEGRATION_GUIDE.md - Technical details
- ../IMPLEMENTATION_COMPLETE.md - Implementation summary

**Last Updated:** 2025-10-29
