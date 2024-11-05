import yaml
import os

def update_leaderboard(problem, score, solution_file, mutation_used, leaderboard_file="leaderboard.yaml", k=5):
    """Updates the leaderboard with problem scores, retaining the top k problems."""
    leaderboard = {}
    if os.path.exists(leaderboard_file):
        with open(leaderboard_file, "r") as file:
            leaderboard = yaml.safe_load(file) or {}

    leaderboard[problem] = {
        "score": score,
        "status": "solved" if score >= 80 else "unsolved",
        "solution_file": solution_file,
        "mutation_used": mutation_used,
        "output": "Execution successful" if score >= 80 else "Execution failed"
    }

    sorted_leaderboard = dict(sorted(leaderboard.items(), key=lambda item: item[1]["score"], reverse=True)[:k])

    with open(leaderboard_file, "w") as file:
        yaml.dump(sorted_leaderboard, file, default_flow_style=False)
    print(f"Leaderboard updated for problem: '{problem}' with score {score}")
