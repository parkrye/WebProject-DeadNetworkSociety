from pathlib import Path

from src.domains.agent.quick_reaction_pool import QuickReactionPool


def test_pick_returns_string() -> None:
    pool = QuickReactionPool()
    result = pool.pick("expert")
    assert isinstance(result, str)
    assert len(result) > 0


def test_pick_all_archetypes() -> None:
    pool = QuickReactionPool()
    archetypes = [
        "expert", "concepter", "provocateur", "storyteller",
        "critic", "cheerleader", "observer", "wildcard",
    ]
    for archetype in archetypes:
        result = pool.pick(archetype)
        assert isinstance(result, str)
        assert len(result) > 0


def test_pick_unknown_archetype_falls_back_to_wildcard() -> None:
    pool = QuickReactionPool()
    result = pool.pick("nonexistent_archetype")
    assert isinstance(result, str)
    assert len(result) > 0


def test_pick_produces_variety() -> None:
    pool = QuickReactionPool()
    results = {pool.pick("wildcard") for _ in range(50)}
    assert len(results) > 1


def test_missing_file_returns_fallback() -> None:
    pool = QuickReactionPool(path=Path("/nonexistent/reactions.yaml"))
    result = pool.pick("expert")
    assert result == "ㅇㅇ"
