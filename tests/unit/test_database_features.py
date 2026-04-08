from __future__ import annotations

from vintagewisdom.models.case import Case
from vintagewisdom.storage.database import Database
from vintagewisdom.utils.helpers import utc_now


def test_database_features(tmp_path) -> None:
    db_path = tmp_path / "test_vintagewisdom.db"
    db = Database(db_path)
    db.initialize()

    tag1_id = db.create_tag("技术债务")
    tag2_id = db.create_tag("架构重构")

    tags = db.list_tags()
    assert len(tags) == 2

    now = utc_now()
    case = Case(
        id="TEST-001",
        domain="TEC",
        title="测试案例",
        description="这是一个测试案例",
        tags=["test", "demo"],
        created_at=now,
        updated_at=now,
    )
    db.insert_case(case)

    db.add_case_tag("TEST-001", tag1_id)
    db.add_case_tag("TEST-001", tag2_id)
    assert len(db.get_case_tags("TEST-001")) == 2

    db.save_case_version(case)
    case.title = "更新后的测试案例"
    db.update_case(case)
    assert len(db.get_case_versions("TEST-001")) >= 1

    case2 = Case(
        id="TEST-002",
        domain="TEC",
        title="测试案例2",
        description="第二个测试案例",
        created_at=now,
        updated_at=now,
    )
    db.insert_case(case2)
    assert db.delete_cases(["TEST-002"]) == 1

    db.create_async_task("task-001", 10)
    db.update_async_task("task-001", status="processing", processed_cases=5)
    task = db.get_async_task("task-001")
    assert task is not None
    assert task["status"] == "processing"
    assert task["processed_cases"] == 5
