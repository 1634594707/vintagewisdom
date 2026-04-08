from __future__ import annotations


def test_plugins_default_load_core_plugins(tmp_path, monkeypatch) -> None:
    from vintagewisdom.core.app import VintageWisdomApp

    monkeypatch.setenv("VW_DATA_DIR", str(tmp_path / "data"))

    app = VintageWisdomApp()
    app.initialize()

    loaded = set(app.plugins.list_loaded())

    # Core built-in plugins should be discoverable and loaded by default.
    assert "storage.sqlite" in loaded
    assert "search.basic" in loaded
