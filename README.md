# Problem Mutation Processor

This project is a Python application designed to load, mutate, and manage problem statements using the Azure OpenAI API. It automates the process of generating, evaluating, and mutating solutions to problems, and then selects the best solutions for each problem.

## Table of Contents
* Features
* Requirements
* Setup Instructions
* Usage
* Testing
* Project Structure
* File Descriptions
* Troubleshooting

# Features
1. Problem Solving: The application generates solutions for problems listed in the problems.txt file.
2. Solution Evaluation: Solutions are filtered based on quality to ensure they meet specific criteria.
3. Solution Mutation: If the first solution isn't adequate, alternative solutions are attempted (mutation).
4. Best Solution Selection: Only the best solutions are kept for each problem.
5. Error Handling: Implements retry logic and exponential backoff for API requests, ensuring resilience in case of failures.

## Requirements
* Python 3.7 or higher
* An API key and endpoint for the Azure OpenAI API

### Setup Instructions
1. Clone the Repository:
- git clone <repository_url>
- cd Assessment

2. Install Dependencies: Install the required Python packages:
- pip install -r requirements.txt

3. Set Up Your API Key and Endpoint: Create a .env file in the project directory with the following content:
- AZURE_API_KEY=your_api_key
- AZURE_ENDPOINT=your_endpoint_url

4. Prepare the problems.txt File: Create or update the problems.txt file with problem statements, one per line. The application will use this file to generate solutions.

#### Usage
* To run the code, simply execute the following command:
python process_problems.py

-- This will process all problems in the problems.txt file, generate solutions, evaluate them, attempt mutations if necessary, and save the best solutions to the output/ directory.

* To test the code, use the following command:
python -m unittest discover tests/

-- This will run all unit tests located in the tests/ directory to ensure that the core functionality works as expected.

#### Testing
We use unit tests to validate the core components of the application. You can run the tests by using:
python -m unittest discover tests/

--This command will discover and run all tests in the tests/ directory.

##### Project Structure
Assessment
├── process_problems.py      # Main script to process problems
├── prompts/                 # Contains prompt templates for the API
│   └── mutations/           # Templates for mutating problems and solutions
├── output/                  # Directory where mutated solutions are saved
├── scripts/
├── problems/                # Folder containing problem statements (problems.txt)
├── leaderboard.yaml         # (Optional) Can be used for tracking scores or rankings
├── leaderboard.py         
├── requirements.txt         # List of dependencies
└── tests/                   # Unit tests to validate functionality

###### File Descriptions

* process_problems.py: The main script that loads problems, generates solutions, evaluates them, attempts mutations, and saves the best solutions.
* prompts/mutations/: Contains templates for problem mutations and solution generation.
* output/: Stores the mutated solutions generated for each problem.
* problems.txt: A text file where each line is a problem statement to be solved.
* leaderboard.yaml: A YAML file (currently optional) that could be used to track the best solutions over time, storing problem names and their corresponding scores.

###### Troubleshooting
- Common Errors
1. API Rate Limiting:

If the program hits the API rate limit, it will automatically retry with exponential backoff (i.e., it will wait longer between retries).

2. YAML Syntax Error:

If there's an error related to leaderboard.yaml, ensure that problem strings are properly quoted to avoid YAML syntax issues. This can be fixed by ensuring that special characters in problem names are wrapped in quotes.

Final Error Handling Review
- File Handling: The program checks if all necessary files (problems.txt, prompt templates) exist before attempting to access them.
- API Requests: We've implemented retries and exponential backoff to handle potential API failures gracefully.
- User Feedback: The program provides helpful feedback in case of failure or retries, making it easier to debug any issues.


