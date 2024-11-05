import os
import uuid
import time
from dotenv import load_dotenv
import subprocess
import random
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
    """Saves a solution as a Python (.py) file in the output directory."""
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist
    unique_id = str(uuid.uuid4())
    file_path = os.path.join(output_dir, f"{unique_id}.py")
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

def execute_solution(file_path, problem):
    """Executes the Python solution file and verifies the output."""
    try:
        result = subprocess.run(["python", file_path], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout.strip()
            
            # Basic output validation
            if not output:
                print("No output generated")
                return False, "No output generated"
                
            # Check if output seems reasonable for the problem
            if "error" in output.lower() or "exception" in output.lower():
                return False, "Error in output"
                
            # Problem-specific validation
            if "prime" in problem.lower() and not any(char.isdigit() for char in output):
                return False, "Expected numeric output for prime number problem"
                
            if "celsius" in problem.lower() and not any(char.isdigit() for char in output):
                return False, "Expected numeric output for temperature conversion"
                
            if "area" in problem.lower() and not any(char.isdigit() for char in output):
                return False, "Expected numeric output for area calculation"
                
            return True, output
        else:
            print(f"Execution failed: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print("Execution timed out.")
        return False, "Timed out"

def generate_population(problem, population_size=3):
    """Generate initial population of solutions."""
    population = []
    for _ in range(population_size):
        # Use different temperatures to encourage diversity
        temperature = 0.3 + (random.random() * 0.4)  # Random temp between 0.3 and 0.7
        solution = generate_solution(problem, temperature=temperature)
        if solution:
            file_path = save_solution(solution)
            population.append({
                'code': solution,
                'file_path': file_path,
                'fitness': 0,
                'generation': 1
            })
    return population

def evaluate_fitness(solution_path, problem):
    """Evaluate fitness of a solution (0-100)."""
    try:
        result = subprocess.run(["python", solution_path], 
                              capture_output=True, text=True, timeout=10)
        
        fitness = 0
        if result.returncode == 0:
            output = result.stdout.strip()
            
            # Basic output validation
            if output:
                fitness += 30  # Program runs and produces output
                
                # Check output matches problem type
                if "prime" in problem.lower() and any(char.isdigit() for char in output):
                    fitness += 20
                elif "celsius" in problem.lower() and any(char.isdigit() for char in output):
                    fitness += 20
                elif "area" in problem.lower() and any(char.isdigit() for char in output):
                    fitness += 20
                
                # Check code quality
                with open(solution_path, 'r') as f:
                    code = f.read()
                    if 'def ' in code:
                        fitness += 10  # Has function definition
                    if code.count('\n') < 20:
                        fitness += 10  # Concise solution
                    if code.count('    ') > code.count('\t'):
                        fitness += 10  # Proper indentation
                    
                # Additional problem-specific checks can be added here
                
        return fitness
        
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return 0

def select_survivors(population, problem, survival_rate=0.5):
    """Select best solutions to survive."""
    for solution in population:
        solution['fitness'] = evaluate_fitness(solution['file_path'], problem)
    
    # Sort by fitness and keep the best ones
    population.sort(key=lambda x: x['fitness'], reverse=True)
    survivors_count = max(1, int(len(population) * survival_rate))
    return population[:survivors_count]

def mutate_survivors(survivors, problem, target_population_size=3, max_attempts=3):
    """Mutate survivors to create new population with better error handling."""
    new_population = survivors.copy()
    attempts = 0
    
    while len(new_population) < target_population_size and attempts < max_attempts:
        attempts += 1
        print(f"\nMutation attempt {attempts}")
        
        # If all previous attempts failed, try more aggressive mutation
        temperature = 0.3 + (attempts * 0.2)  # Increase randomness with each attempt
        
        # Pick a random survivor to mutate
        parent = random.choice(survivors)
        
        # Try different mutation strategies
        if attempts == 1:
            # First try: just rephrase the problem
            mutated_problem, _ = mutate_problem(problem, mutation_type="rephrase")
        elif attempts == 2:
            # Second try: more significant mutation
            mutated_problem, _ = mutate_problem(problem, mutation_type="solve", temperature=temperature)
        else:
            # Last try: completely different approach
            mutated_problem = f"Write a different solution for: {problem}"
        
        if not mutated_problem:
            print("Failed to mutate problem, trying again...")
            continue
            
        print(f"Generated mutated problem: {mutated_problem}")
        
        # Try to generate solution with increased temperature
        mutated_solution = generate_solution(mutated_problem, temperature=temperature)
        if mutated_solution:
            file_path = save_solution(mutated_solution)
            
            # Verify the solution actually works before adding to population
            fitness = evaluate_fitness(file_path, problem)
            if fitness > 0:  # Only add if it has some fitness
                new_population.append({
                    'code': mutated_solution,
                    'file_path': file_path,
                    'fitness': fitness,
                    'generation': parent['generation'] + 1
                })
                print(f"Added new solution with fitness {fitness}")
            else:
                print("Generated solution had zero fitness, trying again...")
        else:
            print("Failed to generate solution, trying again...")
    
    if len(new_population) == 0:
        print("WARNING: Failed to generate any valid solutions after all attempts")
        # Return the original survivors rather than empty population
        return survivors
    
    return new_population

def main():
    problems = load_problems()
    generations = 3  # Number of generations to evolve
    
    for problem in problems:
        print(f"\nProcessing problem: {problem}")
        
        # Generate initial population
        population = generate_population(problem)
        if not population:
            print(f"Failed to generate initial population for problem: {problem}")
            continue
        
        best_fitness = 0
        best_solution = None
        
        for gen in range(generations):
            print(f"\nGeneration {gen + 1}")
            
            # Select survivors
            survivors = select_survivors(population, problem)
            if not survivors:
                print("No survivors in this generation, trying mutation with previous best")
                if best_solution:
                    survivors = [best_solution]
                else:
                    print("No previous best solution, skipping problem")
                    break
            
            # Log results
            for i, solution in enumerate(survivors):
                print(f"Solution {i + 1} fitness: {solution['fitness']}")
                if solution['fitness'] > best_fitness:
                    best_fitness = solution['fitness']
                    best_solution = solution
            
            # Check if we have a good enough solution
            if best_fitness >= 90:
                print(f"Found excellent solution with fitness {best_fitness}")
                update_leaderboard(problem, best_fitness, 
                                 best_solution['file_path'], 
                                 mutation_used=(best_solution['generation'] > 1))
                break
            
            # Create next generation through mutation
            population = mutate_survivors(survivors, problem)
            
            if not population:
                print("Mutation failed to produce valid solutions")
                break
        
        # If we didn't find a great solution, still save the best one we got
        if best_fitness < 90 and best_solution:
            print(f"Saving best solution found with fitness {best_fitness}")
            update_leaderboard(problem, best_fitness,
                             best_solution['file_path'],
                             mutation_used=(best_solution['generation'] > 1))
        
        time.sleep(5)  # Delay between problems

if __name__ == "__main__":
    main()
