from __future__ import annotations


def test_plugins_default_load_demo(tmp_path, monkeypatch) -> None:
    from vintagewisdom.core.app import VintageWisdomApp

    monkeypatch.setenv("VW_DATA_DIR", str(tmp_path / "data"))

    app = VintageWisdomApp()
    app.initialize()

    # demo plugin should be discoverable and loaded by default (unless disabled)
    assert "demo" in app.plugins.list_loaded()
