from agent.core import ResearchAgent

if __name__ == "__main__":
    print("Research Agent ready. Type a goal (or 'quit').")
    agent = ResearchAgent()
    while True:
        goal = input("\nGoal> ").strip()
        if goal.lower() in {"quit", "exit"}:
            break
        if goal:
            print("\n=== FINAL ANSWER ===\n" + agent.run(goal))
