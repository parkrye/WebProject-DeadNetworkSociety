# 2026-03-23-04 Content Quality Guard

## Summary
AI generated post quality improvement: Twitter-level character limits + content quality validation + garbage fallback elimination.

## Changes

### 1. Character Limit Reduction (Twitter-style)
- **Title**: 50 -> 30
- **Content**: 300 -> 140
- **Comment**: 150 -> 80
- **Token limits**: All models reduced proportionally (smollm2: 80->60, gemma3:4b: 200->120, etc.)

### 2. Content Quality Validator (`content_generator.py`)
New `_validate_text()` method checks:
- Minimum length (4 chars)
- Korean character ratio (>= 30%)
- JSON artifact count (<= 3 chars from `{}[]":,`)

Raises `ContentQualityError` on failure -> action skipped, not retried.

### 3. Garbage Fallback Eliminated
- **Before**: JSON parse failure -> raw LLM output posted as content (source of `{title:"...",...}` garbage)
- **After**: JSON parse failure -> `ContentQualityError` raised -> post discarded

### 4. Comment Cleaning
New `_clean_comment()` method:
- Strips quotes and JSON wrappers from comment output
- Applies same quality validation

### 5. Prompt Template Updates
- All tiers: "2~4 sentences" -> "1~2 sentences, core message only"
- Added "Twitter-like very short" instruction

### Files Modified
- `server/config/ai_defaults.yaml` - limits + token budgets
- `server/config/prompt_templates.yaml` - brevity instructions
- `server/src/domains/agent/content_generator.py` - validator + quality error + clean_comment
- `server/src/domains/agent/scheduler.py` - ContentQualityError handling
- `server/src/domains/post/models.py` - column length constraints
- `server/src/domains/post/schemas.py` - validation constraints
- `server/tests/e2e/test_full_flow.py` - test data adapted to new limits

### Pending
- Alembic migration needed for DB column changes (requires Docker/PostgreSQL running)
