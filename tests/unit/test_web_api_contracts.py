from __future__ import annotations

from fastapi.testclient import TestClient


def test_tag_and_batch_delete_contracts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VW_DATA_DIR", str(tmp_path / "data"))

    from vintagewisdom.models.case import Case
    from vintagewisdom.storage.database import Database
    from vintagewisdom.utils.helpers import utc_now
    from vintagewisdom.web.app import create_app

    db_path = tmp_path / "data" / "vintagewisdom.db"
    db = Database(db_path)
    db.initialize()

    now = utc_now()
    db.insert_case(
      Case(
        id="case_contract_1",
        domain="GENERAL",
        title="Contract Test Case",
        created_at=now,
        updated_at=now,
      )
    )

    client = TestClient(create_app())

    create_tag = client.post("/tags", json="important")
    assert create_tag.status_code == 200
    tag_id = create_tag.json()["id"]

    rename_tag = client.put(f"/tags/{tag_id}", json="urgent")
    assert rename_tag.status_code == 200
    assert rename_tag.json()["name"] == "urgent"

    delete_cases = client.post("/cases/batch/delete", json=["case_contract_1"])
    assert delete_cases.status_code == 200
    assert delete_cases.json()["count"] == 1


def test_export_cases_date_filters_accept_aware_timestamps(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VW_DATA_DIR", str(tmp_path / "data"))

    from vintagewisdom.models.case import Case
    from vintagewisdom.storage.database import Database
    from vintagewisdom.utils.helpers import utc_now
    from vintagewisdom.web.app import create_app

    db_path = tmp_path / "data" / "vintagewisdom.db"
    db = Database(db_path)
    db.initialize()

    now = utc_now()
    db.insert_case(
      Case(
        id="case_export_1",
        domain="GENERAL",
        title="Export Filter Case",
        created_at=now,
        updated_at=now,
      )
    )

    client = TestClient(create_app())

    response = client.get("/export/cases", params={"format": "json", "start_date": str(now.date())})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["id"] == "case_export_1"
