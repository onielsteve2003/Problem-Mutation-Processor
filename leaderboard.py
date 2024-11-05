import yaml
import os

def update_leaderboard(problem, score, solution_file, mutation_used, leaderboard_file="leaderboard.yaml", k=5):
    """Updates the leaderboard with problem scores and additional states, retaining only the top k problems."""
    
    # Load the existing leaderboard or initialize an empty dictionary
    leaderboard = {}
    if os.path.exists(leaderboard_file):
        with open(leaderboard_file, "r") as file:
            leaderboard = yaml.safe_load(file) or {}

    # Update or add the current problem in the leaderboard
    leaderboard[problem] = {
        "score": score,
        "status": "solved",  # Mark it as solved when it's added
        "solution_file": solution_file,
        "mutation_used": mutation_used
    }

    # Sort the leaderboard by score in descending order and retain only the top k problems
    sorted_leaderboard = dict(sorted(leaderboard.items(), key=lambda item: item[1]["score"], reverse=True)[:k])

    # Save the updated leaderboard back to the file
    with open(leaderboard_file, "w") as file:
        yaml.dump(sorted_leaderboard, file, default_flow_style=False)

    print(f"Leaderboard updated for problem: '{problem}' with score {score}")
    print(f"Top {k} problems retained in the leaderboard.")
