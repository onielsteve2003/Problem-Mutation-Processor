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

def calculate_kolmogorov_complexity(code):
    """Calculate pure Kolmogorov complexity - simpler is better."""
    # Remove comments and empty lines
    cleaned_lines = []
    for line in code.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Preserve only essential whitespace
            indent = len(line) - len(line.lstrip())
            cleaned_line = ' '.join(word for word in line.split())
            cleaned_lines.append(' ' * indent + cleaned_line)
    
    cleaned_code = '\n'.join(cleaned_lines)
    
    # Simple length-based score (shorter is better)
    max_reasonable_length = 500
    length_score = 70 * (1 - (len(cleaned_code) / max_reasonable_length))
    
    return max(0, length_score)  # Can't go negative

def evaluate_fitness(solution_path, problem):
    """Evaluate fitness based purely on complexity and successful execution."""
    try:
        with open(solution_path, 'r') as f:
            code = f.read()
        
        # Complexity score (70%)
        complexity_score = calculate_kolmogorov_complexity(code)
        
        # Execution score (30%) - just needs to run and produce output
        output, success = execute_solution_safely(solution_path)
        execution_score = 30 if success and output else 0
            
        return complexity_score + execution_score
        
    except Exception as e:
        print(f"Fitness evaluation failed: {e}")
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
    """Mutate survivors with focus on simplification."""
    new_population = survivors.copy()
    attempts = 0
    
    while len(new_population) < target_population_size and attempts < max_attempts:
        attempts += 1
        print(f"\nMutation attempt {attempts}")
        
        # Pick the fittest survivor as parent
        parent = max(survivors, key=lambda x: x['fitness'])
        
        # Progressive mutation strategies
        if attempts == 1:
            # Try to simplify existing solution
            mutated_problem = f"Solve this problem in the simplest way possible: {problem}"
        elif attempts == 2:
            # Try alternative approach
            mutated_problem, _ = mutate_problem(problem, mutation_type="rephrase")
        else:
            # Completely different approach
            mutated_problem = f"Write the shortest possible solution for: {problem}"
        
        temperature = 0.3 + (attempts * 0.1)  # Smaller temperature increments
        mutated_solution = generate_solution(mutated_problem, temperature=temperature)
        
        if mutated_solution:
            file_path = save_solution(mutated_solution)
            fitness = evaluate_fitness(file_path, problem)
            
            # Only accept if it's simpler (higher fitness)
            if fitness > parent['fitness']:
                new_population.append({
                    'code': mutated_solution,
                    'file_path': file_path,
                    'fitness': fitness,
                    'generation': parent['generation'] + 1
                })
                print(f"Added improved solution with fitness {fitness}")
            else:
                print("Solution not better than parent, trying again...")
    
    return new_population if new_population else survivors

def build_docker_image():
    """Build the Docker image for code execution."""
    try:
        subprocess.run(
            ["docker", "build", "-t", "code-runner", "."],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to build Docker image: {e}")
        return False

def execute_solution_safely(file_path):
    """Execute solution in isolated container."""
    container_name = f"code_runner_{uuid.uuid4().hex}"
    
    try:
        # Docker run with strict security constraints
        docker_cmd = [
            "docker", "run",
            "--name", container_name,
            "--rm",  # Remove container after execution
            "--network", "none",  # No network access
            "--memory", "100m",  # Limited memory
            "--cpus", "0.5",  # Limited CPU
            "--pids-limit", "50",  # Limited processes
            "--ulimit", "nofile=64:64",  # Limited file descriptors
            "--security-opt", "no-new-privileges",  # No privilege escalation
            "-v", f"{os.path.abspath(file_path)}:/app/run/code.py:ro",  # Read-only mount
            "code-runner",
            "python", "-I", "/app/run/code.py"
        ]
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return result.stdout.strip(), result.returncode == 0
        
    except Exception as e:
        print(f"Docker execution failed: {e}, falling back to subprocess")
        try:
            # Fallback to subprocess with basic isolation
            result = subprocess.run(
                ["python", "-I", file_path],  # Isolated mode
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip(), result.returncode == 0
        except Exception as sub_e:
            return str(sub_e), False
    finally:
        # Always clean up container
        try:
            subprocess.run(["docker", "rm", "-f", container_name], 
                         capture_output=True)
        except:
            pass

def check_docker_status():
    """Check if Docker daemon is running and accessible."""
    try:
        # Check Docker daemon
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True
        )
        
        # Try to pull base image
        subprocess.run(
            ["docker", "pull", "python:3.9-slim"],
            check=True,
            capture_output=True
        )
        
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:  # Docker not installed
        return False

def main():
    # Check Docker status first
    docker_available = check_docker_status()
    if docker_available:
        if build_docker_image():
            print("Docker environment ready")
        else:
            print("WARNING: Docker available but build failed, using subprocess fallback")
    else:
        print("WARNING: Docker not available, using subprocess fallback")
    
    problems = load_problems()
    generations = 3
    
    for problem in problems:
        print(f"\nProcessing problem: {problem}")
        
        population = generate_population(problem)
        if not population:
            continue
        
        best_fitness = 0
        best_solution = None
        
        for gen in range(generations):
            print(f"\nGeneration {gen + 1}")
            
            survivors = select_survivors(population, problem)
            if not survivors:
                if best_solution:
                    survivors = [best_solution]
                else:
                    break
            
            # Log results and update best
            for solution in survivors:
                print(f"Solution fitness: {solution['fitness']}")
                if solution['fitness'] > best_fitness:
                    best_fitness = solution['fitness']
                    best_solution = solution
            
            if best_fitness >= 90:
                print(f"Found excellent solution with fitness {best_fitness}")
                update_leaderboard(problem, best_fitness, 
                                 best_solution['file_path'], 
                                 mutation_used=(best_solution['generation'] > 1))
                break
            
            population = mutate_survivors(survivors, problem)
            
        # Save best solution even if not perfect
        if best_solution:
            update_leaderboard(problem, best_fitness,
                             best_solution['file_path'],
                             mutation_used=(best_solution['generation'] > 1))
        
        time.sleep(5)  # Rate limiting cooldown

if __name__ == "__main__":
    main()
