"""
Preprocess TL1 conversation data into compact few-shot samples.

Usage:
    python scripts/preprocess_conversations.py <input_dir> <output_file>

Example:
    python scripts/preprocess_conversations.py C:/Users/illuni_61/Downloads/TL1 data/conversation_samples.json
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

SAMPLES_PER_TOPIC = 30
MIN_UTTERANCES = 6
MAX_UTTERANCES = 20
MAX_UTTERANCE_LENGTH = 200

# Map multi_topic prefixes to simplified topic keys
TOPIC_MAP = {
    "안부/일상": "daily",
    "사람/관계": "relationships",
    "생활/행사_반복생활_식사": "food",
    "생활/행사_반복생활_직장": "work",
    "생활/행사_반복생활_가정": "home",
    "생활/행사_반복생활_자연": "nature",
    "생활/행사_반복생활_학교": "school",
    "생활/행사_반복생활_반려동물": "pets",
    "생활/행사_반복생활_공공": "transport",
    "생활/행사_특별생활": "events",
    "사회/경제_쇼핑": "shopping",
    "사회/경제_금융": "finance",
    "사회/경제_자기계발": "self_improvement",
    "사회/경제_시사": "current_affairs",
    "사회/경제_전문분야": "tech",
    "문화/건강_취미/여가_미디어": "media",
    "문화/건강_취미/여가_인물": "celebrity",
    "문화/건강_취미/여가_게임": "gaming",
    "문화/건강_취미/여가_문화생활": "culture",
    "문화/건강_취미/여가_여행": "travel",
    "문화/건강_취미/여가_음악": "music",
    "문화/건강_취미/여가_독서": "books",
    "문화/건강_취미/여가_스포츠": "sports",
    "문화/건강_건강/미용_질병": "health",
    "문화/건강_건강/미용_운동": "fitness",
    "문화/건강_건강/미용_미용": "beauty",
    "문화/건강_건강/미용_건강": "health",
}


def classify_topic(multi_topics: list[str]) -> str:
    """Map multi_topic labels to simplified topic key."""
    for mt in multi_topics:
        for prefix, key in TOPIC_MAP.items():
            if mt.startswith(prefix):
                return key
    return "general"


def extract_conversation(data: dict) -> dict | None:
    """Extract a compact conversation from raw JSON."""
    header = data.get("header", {})
    info = header.get("dialogueInfo", {})
    body = data.get("body", [])

    if not body:
        return None

    utterances = []
    for item in body:
        text = item.get("utterance", "").strip()
        if not text:
            continue
        if len(text) > MAX_UTTERANCE_LENGTH:
            text = text[:MAX_UTTERANCE_LENGTH]
        utterances.append({
            "speaker": item.get("participantID", ""),
            "text": text,
        })

    if len(utterances) < MIN_UTTERANCES:
        return None
    if len(utterances) > MAX_UTTERANCES:
        utterances = utterances[:MAX_UTTERANCES]

    multi_topics = info.get("multi_topic", [])
    topic = classify_topic(multi_topics)

    return {
        "topic": topic,
        "single_topic": info.get("single_topic", ""),
        "utterances": utterances,
    }


def main(input_dir: str, output_file: str) -> None:
    input_path = Path(input_dir)
    output_path = Path(output_file)

    if not input_path.exists():
        print(f"Input directory not found: {input_path}")
        sys.exit(1)

    all_files = list(input_path.rglob("*.json"))
    print(f"Found {len(all_files):,} JSON files")

    # Collect conversations grouped by topic
    by_topic: dict[str, list[dict]] = defaultdict(list)
    errors = 0

    for i, fpath in enumerate(all_files):
        if i % 10000 == 0:
            print(f"  Processing {i:,}/{len(all_files):,}...")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            conv = extract_conversation(data)
            if conv:
                by_topic[conv["topic"]].append(conv)
        except Exception:
            errors += 1

    print(f"Parsed {sum(len(v) for v in by_topic.values()):,} conversations ({errors} errors)")

    # Sample per topic
    result: dict[str, list[dict]] = {}
    for topic, conversations in sorted(by_topic.items()):
        sampled = random.sample(conversations, min(SAMPLES_PER_TOPIC, len(conversations)))
        # Remove topic field from individual items (redundant)
        for conv in sampled:
            del conv["topic"]
        result[topic] = sampled
        print(f"  {topic}: {len(conversations):,} total -> {len(sampled)} sampled")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    file_size = output_path.stat().st_size
    total_samples = sum(len(v) for v in result.values())
    print(f"\nDone: {total_samples} samples across {len(result)} topics")
    print(f"Output: {output_path} ({file_size / 1024:.0f} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
