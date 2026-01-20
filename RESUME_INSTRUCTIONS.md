# 🔄 How to Resume Atlas Personal OS Development

**Use this guide to restart Claude after token refresh or between sessions.**

---

## Quick Resume (Copy-Paste This)

```
I'm continuing work on Atlas Personal OS at /root/atlas-personal-os

Please:
1. Read .claude/CLAUDE.md (project rules)
2. Read .claude/PROGRESS.md (what was done)
3. Read .claude/FEATURES.md (feature status)
4. Continue building the next feature in priority order

Build modules without asking permission. Only report results when complete.
```

---

## Detailed Resume Process

### Step 1: Start New Claude Session

**Open Claude (chat or Claude Code) and paste:**

```
Resume Atlas Personal OS development.

Project location: /root/atlas-personal-os
Read the following files to get context:
- .claude/CLAUDE.md
- .claude/PROGRESS.md
- .claude/FEATURES.md

Then continue building the next high-priority feature.
```

### Step 2: Check What Was Built

**If you want to verify progress first:**

```bash
cd ~/atlas-personal-os
source activate.sh

# Check progress log
cat .claude/PROGRESS.md

# Check feature status
cat .claude/FEATURES.md | grep "active\|complete"

# Run tests to verify what works
pytest tests/ -v

# Test CLI
python main.py --help
```

### Step 3: Tell Claude What to Build

**Option A - Let Claude decide:**
```
Continue building high-priority features from .claude/FEATURES.md
Start with CORE modules, then move to other categories.
```

**Option B - Specify exact feature:**
```
Build feature FIN-001 (Stock Market Data Fetcher) from .claude/FEATURES.md
Include tests and update progress log when complete.
```

**Option C - Build multiple features:**
```
Build features CORE-001, CORE-002, and CORE-003 in sequence.
Run tests after each. Don't stop until all three are complete.
```

---

## What Claude Will Do

When you resume, Claude will:

1. ✅ Read `.claude/CLAUDE.md` (~1000 tokens) - Get project rules
2. ✅ Read `.claude/PROGRESS.md` (~500 tokens) - See what was done
3. ✅ Read `.claude/FEATURES.md` (~2000 tokens) - Check status
4. ✅ Continue exactly where it left off
5. ✅ Build module → Write tests → Update progress
6. ✅ Move to next feature automatically

---

## For Long Autonomous Work Sessions

**If using Claude Code:**

```bash
cd ~/atlas-personal-os
claude chat
```

Then paste:
```
Build all HIGH priority features from .claude/FEATURES.md in order.
For each feature:
1. Build the module
2. Write pytest tests
3. Run tests and verify they pass
4. Update .claude/PROGRESS.md
5. Move to next feature

Work autonomously until all HIGH priority features are complete.
Use .claudeconfig settings (already configured for auto-approval).
```

---

## Checking Progress Remotely

**Before you leave, note the current state:**

```bash
cd ~/atlas-personal-os

# Save current progress to a file you can check later
cat .claude/PROGRESS.md > ~/atlas_snapshot_$(date +%Y%m%d_%H%M).txt

# Or email it to yourself (setup tomorrow with progress_emailer.py)
```

**When you return:**

```bash
cd ~/atlas-personal-os

# See what changed
git diff .claude/PROGRESS.md  # If using git

# Or just read it
cat .claude/PROGRESS.md

# Test what was built
pytest tests/ -v
```

---

## Token Management Strategy

**Session 1 (Now - 52k tokens left):**
- Build CORE-001 + CORE-002 (foundation)
- Update progress log

**Session 2 (After 5 hour refresh):**
- Resume with instructions above
- Build 2-3 more features
- Update progress log

**Session 3 (After next refresh):**
- Continue with next priority features

**Each session builds on the last because:**
- `.claude/PROGRESS.md` tracks everything
- `.claude/FEATURES.md` shows status
- Tests verify nothing broke

---

## Emergency Recovery

**If something breaks:**

```
I'm resuming Atlas Personal OS but something seems broken.

Please:
1. Read .claude/PROGRESS.md to see what was attempted
2. Run pytest tests/ -v to see what's failing
3. Read the failing test output
4. Fix the issue
5. Re-run tests until passing
6. Update progress log
```

---

## Template Messages for Different Scenarios

### "I want to build a specific feature"
```
Resume Atlas Personal OS at /root/atlas-personal-os
Build feature [FEATURE-ID] from .claude/FEATURES.md
Include tests and update progress when complete.
```

### "Just keep building until done"
```
Resume Atlas Personal OS at /root/atlas-personal-os
Read .claude/PROGRESS.md and continue building features in priority order.
Work autonomously. Report summary when done or tokens run low.
```

### "Something went wrong, fix it"
```
Resume Atlas Personal OS at /root/atlas-personal-os
Read .claude/PROGRESS.md to see what was last attempted.
Run tests to identify failures.
Fix all failing tests.
```

### "Show me a summary of progress"
```
Resume Atlas Personal OS at /root/atlas-personal-os
Read .claude/PROGRESS.md and .claude/FEATURES.md
Give me a summary of:
- What features are complete
- What's in progress
- What's next
- Current test status
```

---

## Best Practices

✅ **DO:**
- Start each session by reading `.claude/PROGRESS.md`
- Run `pytest tests/ -v` before and after building
- Update progress log after each feature
- Use specific feature IDs (CORE-001, FIN-002, etc.)

❌ **DON'T:**
- Assume Claude remembers previous sessions (it doesn't)
- Skip reading the .claude/ files
- Build without tests
- Forget to activate virtual environment (`source activate.sh`)

---

## Quick Reference Commands

```bash
# Activate environment
cd ~/atlas-personal-os && source activate.sh

# Check progress
cat .claude/PROGRESS.md

# Check feature status  
cat .claude/FEATURES.md

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_database.py -v

# Test CLI
python main.py --help

# Format code
black .

# Lint code
ruff check .
```

---

## Files to Read Each Session

**Minimum (fast resume):**
- `.claude/PROGRESS.md` (what happened last)

**Recommended (full context):**
- `.claude/CLAUDE.md` (project rules)
- `.claude/PROGRESS.md` (history)
- `.claude/FEATURES.md` (status)

**Optional (deep dive):**
- `.claude/MODULES.md` (architecture)
- `README.md` (documentation)

---

## Success Criteria

**You know it's working when:**
- ✅ Tests pass: `pytest tests/` shows green
- ✅ CLI works: `python main.py --help` shows commands
- ✅ Features marked complete in `.claude/FEATURES.md`
- ✅ Progress log updated with details
- ✅ No errors when running modules

---

## Next Session Checklist

Before you resume, make sure:
- [ ] You're in the right directory (`cd ~/atlas-personal-os`)
- [ ] Virtual environment activated (`source activate.sh`)
- [ ] You know which feature to build (or let Claude decide)
- [ ] You have the resume prompt ready (copy from above)

**You're ready to resume! Just paste the Quick Resume prompt when you return.**
