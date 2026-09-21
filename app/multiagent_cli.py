"""Offline CLI for smoke-testing JARVIS multi-agent routing."""

from app.core.multiagent import build_demo_runtime


def main() -> None:
    runtime = build_demo_runtime()
    print("JARVIS multi-agent demo. Type 'exit' to quit.")
    while True:
        task = input("\nYou: ").strip()
        if task.lower() in {"exit", "quit"}:
            print("JARVIS: Session ended.")
            return
        if not task:
            continue

        context = runtime.run(task)
        print(f"JARVIS [{context.route}]: {context.artifacts.get(context.route, 'No specialist output')}")
        print(f"Verification: {context.artifacts.get('verification', 'not-run')}")
        print(f"Events: {' -> '.join(context.events)}")


if __name__ == "__main__":
    main()
