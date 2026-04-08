from __future__ import annotations

from vintagewisdom.core.retriever import Retriever
from vintagewisdom.models.case import Case
from vintagewisdom.utils.helpers import utc_now


class DummyDB:
    def __init__(self, cases):
        self._cases = cases

    def list_cases(self):
        return list(self._cases)


def test_retriever_skips_test_cases() -> None:
    now = utc_now()
    retriever = Retriever(
        DummyDB(
            [
                Case(
                    id="case_test_123",
                    domain="GENERAL",
                    title="Test Case",
                    description="Just a test",
                    created_at=now,
                    updated_at=now,
                ),
                Case(
                    id="CAR-001",
                    domain="CAR",
                    title="职业选择中的长期成长权衡",
                    description="比较新 offer 和当前岗位的成长空间",
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
    )

    results = retriever.retrieve("成长空间", top_k=5)

    assert len(results) == 1
    assert results[0].id == "CAR-001"
