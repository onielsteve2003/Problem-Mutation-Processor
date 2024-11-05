import os
import time
import requests
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

def mutate_problem(problem, mutation_type="rephrase", temperature=0.7, max_tokens=800):
    """Mutates a problem using Azure OpenAI API and a prompt template."""
    prompt_template = load_prompt(mutation_type)
    prompt = prompt_template.format(problem=problem)

    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }

    payload = {
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": "You are an algorithmic expert and the best coder in the world"}]},
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "temperature": temperature,  # Allow dynamic temperature
        "top_p": 0.95,
        "max_tokens": max_tokens  # Allow dynamic max_tokens
    }

    for attempt in range(5):  # Retry up to 5 times
        try:
            response = requests.post(ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()  # Check for HTTP errors
            
            # Parse and return response content
            completion = response.json()
            return completion['choices'][0]['message']['content'].strip(), mutation_type  # Return mutation type as well

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            wait_time = 2 ** attempt
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break
            
    return None, mutation_type  # Return mutation type in case of failure

def generate_solution(problem, mutation_type="solve"):
    """Generates a solution for a problem using Azure OpenAI API and a prompt template."""
    prompt_template = load_prompt(mutation_type)
    prompt = prompt_template.format(problem=problem)
    
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }

    payload = {
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": "You are an algorithmic expert and the best coder in the world"}]},
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    for attempt in range(5):  # Retry up to 5 times
        try:
            response = requests.post(ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()  # Check for HTTP errors
            
            # Parse and return response content
            completion = response.json()
            return completion['choices'][0]['message']['content'].strip()

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            wait_time = 2 ** attempt
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break
    return None  # Return None if all retries fail
