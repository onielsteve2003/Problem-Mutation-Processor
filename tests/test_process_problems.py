import unittest
from unittest.mock import patch
import os
import yaml
from process_problems import load_problems, evaluate_solution, save_solution, update_leaderboard
from prompts.mutations.mutation import generate_solution

class TestProcessProblems(unittest.TestCase):

    def test_load_problems(self):
        """Test if problems are loaded correctly from the file."""
        problems = load_problems("problems/problems.txt")
        self.assertIsInstance(problems, list)
        self.assertGreater(len(problems), 0, "No problems found in problems.txt")

    def test_load_problems_empty_file(self):
        """Test loading from an empty problems file."""
        with open("problems/empty_problems.txt", "w") as file:
            file.write("")  # Create an empty file
        problems = load_problems("problems/empty_problems.txt")
        self.assertEqual(problems, [], "Expected an empty list for an empty problems file.")
        os.remove("problems/empty_problems.txt")  # Cleanup

    def test_load_problems_file_not_found(self):
        """Test loading from a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_problems("problems/non_existent_file.txt")

    @patch('prompts.mutations.mutation.requests.post')
    def test_generate_solution(self, mock_post):
        """Test if a solution is generated for a sample problem with mocked response."""
        problem = "Solve the equation x + 2 = 10."
        mock_post.return_value.json.return_value = {
            'choices': [{'message': {'content': 'The solution is x = 8.'}}]
        }
        solution = generate_solution(problem)
        self.assertIsNotNone(solution, "Failed to generate a solution for the problem")
        self.assertEqual(solution, 'The solution is x = 8.', "Generated solution does not match expected value.")

    def test_evaluate_solution(self):
        """Test if the solution evaluation function works as expected."""
        valid_solution = "The solution is x = 8."
        invalid_solution = "Solve for x."
        self.assertTrue(evaluate_solution(valid_solution), "Valid solution was not accepted")
        self.assertFalse(evaluate_solution(invalid_solution), "Invalid solution was incorrectly accepted")

    def test_save_solution(self):
        """Test if the solution is saved correctly in the output directory."""
        solution = "The solution to the problem is x = 8."
        file_path = save_solution(solution, output_dir="output_test")
        self.assertTrue(os.path.exists(file_path), "Solution file was not saved")

        with open(file_path, "r") as file:
            content = file.read()
            self.assertEqual(content, solution, "Saved content does not match the expected solution.")
        
        # Cleanup
        os.remove(file_path)

    def test_update_leaderboard(self):
        """Test updating the leaderboard."""
        update_leaderboard("Problem 1", 100, "solution1.txt", False, "leaderboard_test.yaml", k=3)
        update_leaderboard("Problem 2", 80, "solution2.txt", False, "leaderboard_test.yaml", k=3)
        update_leaderboard("Problem 3", 90, "solution3.txt", False, "leaderboard_test.yaml", k=3)
        update_leaderboard("Problem 4", 70, "solution4.txt", False, "leaderboard_test.yaml", k=3)

        with open("leaderboard_test.yaml", "r") as file:
            leaderboard = yaml.safe_load(file)
            
        self.assertEqual(len(leaderboard), 3, "Leaderboard should retain only the top 3 problems.")
        self.assertIn("Problem 1", leaderboard, "Problem 1 should be in the leaderboard.")
        self.assertIn("Problem 3", leaderboard, "Problem 3 should be in the leaderboard.")
        self.assertNotIn("Problem 4", leaderboard, "Problem 4 should not be in the leaderboard.")

        os.remove("leaderboard_test.yaml")  # Cleanup

if __name__ == "__main__":
    unittest.main()
