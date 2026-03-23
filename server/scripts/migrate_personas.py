"""Migration script: add imperfection_level, length_range to all persona YAMLs,
and remove English personality field (writing_style + archetype_detail are sufficient).
"""
import re
from pathlib import Path

PERSONAS_DIR = Path(__file__).resolve().parent.parent / "data" / "personas"

# Archetype -> default imperfection_level mapping
# Higher for casual archetypes, lower for formal ones
ARCHETYPE_IMPERFECTION: dict[str, int] = {
    "expert": 2,
    "concepter": 3,
    "provocateur": 6,
    "storyteller": 3,
    "critic": 2,
    "cheerleader": 5,
    "observer": 1,
    "wildcard": 7,
}

# Archetype -> default length_range
ARCHETYPE_LENGTH: dict[str, list[int]] = {
    "expert": [2, 5],
    "concepter": [3, 6],
    "provocateur": [1, 3],
    "storyteller": [3, 6],
    "critic": [2, 4],
    "cheerleader": [1, 3],
    "observer": [1, 2],
    "wildcard": [1, 4],
}

# Model size affects imperfection: smaller models get slight boost
# since their output is already less polished
MODEL_IMPERFECTION_BONUS: dict[str, int] = {
    "smollm2": 2,
    "llama3.2:1b": 1,
    "qwen2:1.5b": 1,
    "qwen3:1.7b": 0,
    "gemma2:2b": 0,
    "exaone3.5:2.4b": 0,
    "phi3:mini": 0,
    "gemma3:4b": 0,
}


def migrate_file(file_path: Path) -> bool:
    """Add imperfection_level and length_range. Remove personality field.
    Returns True if file was modified.
    """
    content = file_path.read_text(encoding="utf-8")

    # Skip if already migrated
    if "imperfection_level:" in content:
        return False

    # Extract archetype
    archetype_match = re.search(r'^archetype:\s*(\w+)', content, re.MULTILINE)
    archetype = archetype_match.group(1) if archetype_match else "wildcard"

    # Extract model
    model_match = re.search(r'^model:\s*["\']?([^"\'"\n]+)', content, re.MULTILINE)
    model = model_match.group(1).strip() if model_match else ""

    # Calculate imperfection level
    base = ARCHETYPE_IMPERFECTION.get(archetype, 3)
    bonus = MODEL_IMPERFECTION_BONUS.get(model, 0)
    imperfection = min(10, base + bonus)

    # Get length range
    length_range = ARCHETYPE_LENGTH.get(archetype, [2, 4])

    # Remove the English personality block
    # personality is a multi-line YAML field with > or | or quoted string
    content = re.sub(
        r'^personality:\s*>[\s\S]*?(?=^\w)',
        '',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^personality:\s*\|[\s\S]*?(?=^\w)',
        '',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    # Single-line personality
    content = re.sub(
        r'^personality:\s*"[^"]*"\n',
        '',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^personality:\s*'[^']*'\n",
        '',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    # Add new fields before 'examples:' or 'preferences:' or at end
    new_fields = (
        f"imperfection_level: {imperfection}\n"
        f"length_range: [{length_range[0]}, {length_range[1]}]\n"
    )

    if "examples:" in content:
        content = content.replace("examples:", f"{new_fields}examples:")
    elif "preferences:" in content:
        content = content.replace("preferences:", f"{new_fields}preferences:")
    else:
        content = content.rstrip() + "\n" + new_fields

    file_path.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    if not PERSONAS_DIR.exists():
        print(f"Personas directory not found: {PERSONAS_DIR}")
        return

    modified = 0
    total = 0
    for file_path in sorted(PERSONAS_DIR.rglob("*.yaml")):
        if file_path.name.startswith("_"):
            continue
        total += 1
        try:
            if migrate_file(file_path):
                modified += 1
                print(f"  Migrated: {file_path.relative_to(PERSONAS_DIR)}")
            else:
                print(f"  Skipped (already migrated): {file_path.relative_to(PERSONAS_DIR)}")
        except Exception as e:
            print(f"  ERROR: {file_path.relative_to(PERSONAS_DIR)}: {e}")

    print(f"\nDone: {modified}/{total} files migrated")


if __name__ == "__main__":
    main()
