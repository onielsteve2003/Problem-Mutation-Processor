import os
import uuid
import time
from dotenv import load_dotenv
from prompts.mutations.mutation import generate_solution, mutate_problem
from leaderboard import update_leaderboard 

# Load environment variables from .env file
load_dotenv()

def load_problems(file_path="problems/problems.txt"):
    """Loads problems from a text file, each line is a problem."""
    if not os.path.exists(file_path):
        raise FileNotFoundError("The problems.txt file is missing!")
    with open(file_path, "r") as file:
        problems = file.readlines()
    return [problem.strip() for problem in problems]

def save_solution(solution, output_dir="output/"):
    """Saves a solution to a unique file in the output directory."""
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist
    unique_id = str(uuid.uuid4())  # Generate a unique filename
    file_path = os.path.join(output_dir, f"{unique_id}.txt")
    with open(file_path, "w", encoding='utf-8') as file:  # Specify UTF-8 encoding
        file.write(solution)  # Save solution to file
    return file_path

def evaluate_solution(solution):
    """Basic evaluation to check if the solution is adequate."""
    # Check if the solution is a string, has a minimum length, and is a valid response
    return (
        isinstance(solution, str) and
        len(solution.strip()) > 5 and  # Relax the length condition slightly
        "Solve" not in solution and
        "not valid" not in solution.lower() and
        "error" not in solution.lower() and
        "undefined" not in solution.lower() and
        "invalid" not in solution.lower() and
        "incorrect" not in solution.lower()  # Added 'incorrect' for further flexibility
    )

def main():
    # Load problems from file
    problems = load_problems()
    max_problems_to_process = 5
    processed_count = 0

    for problem in problems:
        if processed_count >= max_problems_to_process:
            break  # Stop if we reach the limit for this run

        try:
            # Step 1: Attempt to generate a solution
            solution = generate_solution(problem)
            if solution is None:
                print(f"Failed to generate solution for problem: '{problem}'. Skipping...")
                continue

            # Step 2: Evaluate solution quality
            if evaluate_solution(solution):
                file_path = save_solution(solution)  # Save the valid solution
                print(f"Saved valid solution to {file_path}")
                score = 100
                update_leaderboard(problem, score, file_path, mutation_used=False)  # No mutation used
                processed_count += 1
            else:
                # Step 3: If solution is inadequate, mutate and retry
                print(f"Solution for '{problem}' is inadequate. Retrying with mutation...")
                
                # Generate a mutated problem
                mutated_problem = mutate_problem(problem)  # Add mutation step here
                mutated_solution = generate_solution(mutated_problem)
                
                if mutated_solution and evaluate_solution(mutated_solution):
                    file_path = save_solution(mutated_solution)
                    print(f"Saved improved solution to {file_path}")
                    score = 80  # Example score for mutated solutions
                    update_leaderboard(problem, score, file_path, mutation_used=True)  # Mutation used
                    processed_count += 1
                else:
                    print(f"Failed to find adequate solution for problem: '{problem}'")

        except Exception as e:
            print(f"An error occurred while processing problem '{problem}': {e}")

        time.sleep(10)  # Longer wait time between requests

if __name__ == "__main__":
    main()
