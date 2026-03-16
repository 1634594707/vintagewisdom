from __future__ import annotations


def run_tui() -> None:
    from datetime import datetime

    from ..core.app import VintageWisdomApp
    from ..models.case import Case

    app = VintageWisdomApp()
    app.initialize()
    engine = app.engine

    def help_text() -> str:
        return (
            "Commands:\n"
            "  query <text>        - query similar cases\n"
            "  add-case            - add a case interactively\n"
            "  stats               - show stats\n"
            "  help                - show help\n"
            "  exit                - quit\n"
        )

    print("VintageWisdom TUI (REPL)\n" + help_text())
    while True:
        try:
            line = input("vw> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return

        if not line:
            continue
        if line in {"exit", "quit", ":q"}:
            print("bye")
            return
        if line == "help":
            print(help_text())
            continue
        if line == "stats":
            print(f"Cases: {engine.db.count_cases()}")
            print(f"DecisionLogs: {engine.db.count_decision_logs()} (evaluated: {engine.db.count_evaluated_decision_logs()})")
            continue
        if line.startswith("query "):
            q = line[len("query ") :].strip()
            if not q:
                continue
            r = engine.query(q)
            print(f"Matches: {len(r.cases)}")
            for c in r.cases:
                print(f"- {c.id}: {c.title}")
            print("Reasoning:")
            print(r.reasoning)
            if r.recommendations:
                print("Recommendations:")
                for item in r.recommendations:
                    print(f"- {item}")
            continue
        if line == "add-case":
            try:
                cid = input("id: ").strip()
                dom = input("domain (HIS/FIN/CAR/TEC or GENERAL): ").strip() or "GENERAL"
                title = input("title: ").strip()
                desc = input("description: ").strip()
                if not cid or not title:
                    print("id/title required")
                    continue
                now = datetime.utcnow()
                engine.add_case(
                    Case(
                        id=cid,
                        domain=dom,
                        title=title,
                        description=desc or None,
                        created_at=now,
                        updated_at=now,
                    )
                )
                print("ok")
            except Exception as e:
                print(f"failed: {e}")
            continue

        print("unknown command, type 'help'")
