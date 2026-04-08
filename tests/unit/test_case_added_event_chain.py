from __future__ import annotations


def test_case_added_event_chain_does_not_crash(tmp_path, monkeypatch) -> None:
    from vintagewisdom.core.app import VintageWisdomApp
    from vintagewisdom.core.events import events
    from vintagewisdom.models.case import Case
    from vintagewisdom.utils.helpers import utc_now

    monkeypatch.setenv("VW_DATA_DIR", str(tmp_path / "data"))

    app = VintageWisdomApp()
    app.initialize()

    seen = {"case_added": 0, "db_inserted": 0}

    def on_case_added(e) -> None:
        seen["case_added"] += 1

    def on_db_case_inserted(e) -> None:
        seen["db_inserted"] += 1

    events.on("case.added", on_case_added)
    events.on("db.case.inserted", on_db_case_inserted)

    now = utc_now()
    c = Case(
        id=f"case_test_{int(now.timestamp())}",
        domain="GENERAL",
        title="Test Case",
        description="Just a test",
        created_at=now,
        updated_at=now,
    )

    # Should not raise even if AI/KG plugins are enabled but unavailable.
    app.engine.add_case(c)

    assert seen["case_added"] >= 1
    assert seen["db_inserted"] >= 1
