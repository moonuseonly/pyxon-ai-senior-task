"""
Entry point.

Run the benchmark:
    python main.py

Ask a single question:
    python main.py "What is the current weather in Riyadh?"
"""
import sys
from src.graph import swarm


def run_benchmark():
    test_cases = [
        {"question": "What is 15% of 200", "expect_route": "direct"},
        {"question": "What is the current weather in Riyadh?", "expect_route": "research"},
        {
            "question": "What does the API at https://api.github.com/repos/langchain-ai/langgraph return?",
            "expect_route": "research",
        },
    ]

    print("\n" + "=" * 50)
    print("BENCHMARK")
    print("=" * 50)

    for case in test_cases:
        result = swarm.invoke({"question": case["question"]})
        route_ok = result["route"] == case["expect_route"]
        status = "PASS" if route_ok else "FAIL"
        print(f"\n[{status}] {case['question']}")
        print(f"  Expected route: {case['expect_route']}, Got: {result['route']}")
        print(f"  Answer: {result['final_answer']}")


def ask(question: str):
    result = swarm.invoke({"question": question})
    print(f"\nRoute: {result['route']}")
    print(f"Answer: {result['final_answer']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ask(" ".join(sys.argv[1:]))
    else:
        run_benchmark()
