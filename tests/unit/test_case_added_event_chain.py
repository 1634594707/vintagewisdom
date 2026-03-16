from __future__ import annotations


def test_case_added_event_chain_does_not_crash() -> None:
    from datetime import datetime

    from vintagewisdom.core.app import VintageWisdomApp
    from vintagewisdom.core.events import events
    from vintagewisdom.models.case import Case

    app = VintageWisdomApp()
    app.initialize()

    seen = {"case_added": 0, "db_inserted": 0}

    def on_case_added(e) -> None:
        seen["case_added"] += 1

    def on_db_case_inserted(e) -> None:
        seen["db_inserted"] += 1

    events.on("case.added", on_case_added)
    events.on("db.case.inserted", on_db_case_inserted)

    c = Case(
        id=f"case_test_{int(datetime.utcnow().timestamp())}",
        domain="GENERAL",
        title="Test Case",
        description="Just a test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Should not raise even if AI/KG plugins are enabled but unavailable.
    app.engine.add_case(c)

    assert seen["case_added"] >= 1
    assert seen["db_inserted"] >= 1
