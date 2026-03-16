from __future__ import annotations


def test_plugins_default_load_demo() -> None:
    from vintagewisdom.core.app import VintageWisdomApp

    app = VintageWisdomApp()
    app.initialize()

    # demo plugin should be discoverable and loaded by default (unless disabled)
    assert "demo" in app.plugins.list_loaded()
