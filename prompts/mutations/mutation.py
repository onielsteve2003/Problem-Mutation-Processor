import os
import time
import requests
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")

def load_prompt(mutation_type="solve"):
    """Loads a mutation template prompt from the prompts folder."""
    prompt_path = f"prompts/mutations/{mutation_type}.txt"
    with open(prompt_path, "r") as file:
        return file.read()

def mutate_problem(problem, mutation_type="rephrase", max_retries=5):
    """Mutates a problem with exponential backoff for API calls."""
    prompt_template = load_prompt(mutation_type)
    prompt = prompt_template.format(problem=problem)

    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }

    payload = {
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": """You are an expert Python programmer focused on generating clean, correct code.
Rules:
1. Always use 4-space indentation
2. Initialize all variables
3. Include complete function definitions
4. Test the code with example inputs
5. Return only valid Python code
6. No explanatory text or comments
7. No markdown formatting"""}]},
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "temperature": 0.7,  # Allow dynamic temperature
        "top_p": 0.95,
        "max_tokens": 800  # Allow dynamic max_tokens
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip(), mutation_type
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (2 ** attempt) + random.uniform(0, 1)  # Add jitter
                print(f"Rate limited. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                continue
            raise
    return None, mutation_type

def generate_solution(problem, mutation_type="solve", temperature=0.3, max_attempts=3):
    """Generates a Python solution for a problem using Azure OpenAI API."""
    for attempt in range(max_attempts):
        prompt_template = load_prompt(mutation_type)
        prompt = prompt_template.format(problem=problem)
        
        headers = {
            "Content-Type": "application/json",
            "api-key": API_KEY,
        }

        payload = {
            "messages": [
                {"role": "system", "content": [{"type": "text", "text": """You are an expert Python programmer focused on generating clean, correct code.
Rules:
1. Always use 4-space indentation
2. Initialize all variables
3. Include complete function definitions
4. Test the code with example inputs
5. Return only valid Python code
6. No explanatory text or comments
7. No markdown formatting"""}]},
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
            "temperature": temperature,  # Use the passed temperature parameter
            "top_p": 1,
            "max_tokens": 800
        }

        try:
            response = requests.post(ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            
            completion = response.json()
            code = completion['choices'][0]['message']['content'].strip()
            
            # Remove markdown formatting if present
            if "```python" in code or "```" in code:
                code = code.replace("```python", "").replace("```", "").strip()

            # Validate code
            try:
                # Try to compile the code
                compile(code, '<string>', 'exec')
                
                # Check indentation
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        # Skip top-level definitions
                        if line.startswith('def ') or line.startswith('import ') or line.startswith('from '):
                            continue
                            
                        # Check if line needs indentation
                        prev_line = lines[i-1] if i > 0 else ''
                        if prev_line.strip().endswith(':'):
                            if not line.startswith('    '):
                                raise IndentationError(f"Missing indentation after '{prev_line.strip()}'")
                
                # If we get here, code is valid
                return code

            except (SyntaxError, IndentationError) as e:
                print(f"Validation failed on attempt {attempt + 1}: {e}")
                if attempt == max_attempts - 1:
                    print("All attempts failed to generate valid code")
                    return None
                continue

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if attempt == max_attempts - 1:
                return None
            time.sleep(2 ** attempt)  # Exponential backoff

    return None
