import unittest
import sys
import os

# Add the parent directory to sys.path to import app functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import select_characters, load_characters


class TestCharacterSelection(unittest.TestCase):
    
    def setUp(self):
        # Load real data for testing
        try:
            self.all_chars = load_characters()
            print(f"\n--- Real Data Loaded ---")
            print(f"Total characters in data.txt: {len(self.all_chars)}")
            print(f"First 20 chars: {self.all_chars[:20]}")
            print(f"Chars 50-55: {self.all_chars[50:56]}")
            print(f"Last 10 chars: {self.all_chars[-10:]}")
        except FileNotFoundError:
            self.fail("data.txt not found - required for tests")
    
    def test_normal_case_valid_input(self):
        """Test normal case with valid inputs following all rules"""
        print(f"\n=== Test: Normal valid case ===")
        
        # Use characters from indices > 50
        if len(self.all_chars) < 55:
            self.skipTest("Need at least 55 characters in data.txt")
            
        new_chars = self.all_chars[52:55]  # indices 52, 53, 54
        start_char = self.all_chars[30]     # index 30 (< 52)
        
        print(f"Input - New chars: '{new_chars}' (indices: 52,53,54)")
        print(f"Input - Start char: '{start_char}' (index: 30)")
        print(f"Need {50 - len(new_chars)} old characters")
        
        result = select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Result length: {len(result)}")
        print(f"New chars in result: {result[:len(new_chars)]}")
        print(f"First 10 old chars: {result[len(new_chars):len(new_chars)+10]}")
        print(f"Last 10 old chars: {result[-10:]}")
        
        # Verify result
        self.assertEqual(len(result), 50)
        self.assertEqual(result[:len(new_chars)], list(new_chars))
        
        # Verify no duplicates
        self.assertEqual(len(set(result)), 50, "Result contains duplicates")
        
        # Verify old chars start from index 30 and count backwards
        old_chars = result[len(new_chars):]
        self.assertEqual(old_chars[0], self.all_chars[30], "First old char should be at start index")
    
    def test_new_char_not_in_data(self):
        """Test error when new character not in data.txt"""
        print(f"\n=== Test: New char not in data ===")
        
        new_chars = "🚀💫"  # Characters not in data.txt
        start_char = self.all_chars[10]
        
        print(f"Input - New chars: '{new_chars}' (not in data)")
        print(f"Input - Start char: '{start_char}'")
        
        with self.assertRaises(ValueError) as context:
            select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Expected error: {context.exception}")
        self.assertIn("not found in data.txt", str(context.exception))
    
    def test_new_char_index_too_small(self):
        """Test error when new character index <= 50"""
        print(f"\n=== Test: New char index <= 50 ===")
        
        # Use character from early in data (index <= 50)
        new_chars = self.all_chars[20:22]  # indices 20, 21
        start_char = self.all_chars[10]
        
        print(f"Input - New chars: '{new_chars}' (indices: 20,21 - should be > 50)")
        print(f"Input - Start char: '{start_char}'")
        
        with self.assertRaises(ValueError) as context:
            select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Expected error: {context.exception}")
        self.assertIn("must have indices > 50", str(context.exception))
    
    def test_start_char_not_in_data(self):
        """Test error when start character not in data.txt"""
        print(f"\n=== Test: Start char not in data ===")
        
        if len(self.all_chars) < 55:
            self.skipTest("Need at least 55 characters in data.txt")
            
        new_chars = self.all_chars[52:54]
        start_char = "🎯"  # Not in data.txt
        
        print(f"Input - New chars: '{new_chars}'")
        print(f"Input - Start char: '{start_char}' (not in data)")
        
        with self.assertRaises(ValueError) as context:
            select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Expected error: {context.exception}")
        self.assertIn("not found in data.txt", str(context.exception))
    
    def test_empty_start_char(self):
        """Test error when start character is empty"""
        print(f"\n=== Test: Empty start char ===")
        
        if len(self.all_chars) < 55:
            self.skipTest("Need at least 55 characters in data.txt")
            
        new_chars = self.all_chars[52:54]
        start_char = ""
        
        print(f"Input - New chars: '{new_chars}'")
        print(f"Input - Start char: '{start_char}' (empty)")
        
        with self.assertRaises(ValueError) as context:
            select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Expected error: {context.exception}")
        self.assertIn("is required", str(context.exception))
    
    def test_start_index_too_large(self):
        """Test error when start index >= min new char index"""
        print(f"\n=== Test: Start index >= min new char index ===")
        
        if len(self.all_chars) < 55:
            self.skipTest("Need at least 55 characters in data.txt")
            
        new_chars = self.all_chars[52:54]  # indices 52, 53
        start_char = self.all_chars[52]    # index 52 (same as min new index)
        
        print(f"Input - New chars: '{new_chars}' (indices: 52,53)")
        print(f"Input - Start char: '{start_char}' (index: 52 - should be < 52)")
        
        with self.assertRaises(ValueError) as context:
            select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Expected error: {context.exception}")
        self.assertIn("must be less than smallest new character index", str(context.exception))
    
    def test_wraparound_case(self):
        """Test case where we need to wrap around to end of data"""
        print(f"\n=== Test: Wraparound case ===")
        
        if len(self.all_chars) < 100:
            self.skipTest("Need at least 100 characters for this test")
            
        # Use new chars from late in data, start char early
        new_chars = self.all_chars[80:82]  # indices 80, 81
        start_char = self.all_chars[5]     # index 5
        
        print(f"Input - New chars: '{new_chars}' (indices: 80,81)")
        print(f"Input - Start char: '{start_char}' (index: 5)")
        print(f"Need {50 - len(new_chars)} old characters")
        print(f"Should wrap around: 5,4,3,2,1,0, then from end backwards")
        
        result = select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Result length: {len(result)}")
        print(f"New chars: {result[:len(new_chars)]}")
        print(f"First 10 old chars: {result[len(new_chars):len(new_chars)+10]}")
        print(f"Last 10 old chars: {result[-10:]}")
        
        # Verify result
        self.assertEqual(len(result), 50)
        self.assertEqual(result[:len(new_chars)], list(new_chars))
        
        # Verify no duplicates
        self.assertEqual(len(set(result)), 50, "Result contains duplicates")
        
        # Check that it starts from index 5 and wraps correctly
        old_chars = result[len(new_chars):]
        self.assertEqual(old_chars[0], self.all_chars[5])
        
        # Should have characters from both beginning and end
        old_char_indices = [self.all_chars.index(char) for char in old_chars]
        print(f"Old char indices (first 20): {old_char_indices[:20]}")
        print(f"Old char indices (last 10): {old_char_indices[-10:]}")
    
    def test_exactly_50_new_chars(self):
        """Test when exactly 50 new characters are provided"""
        print(f"\n=== Test: Exactly 50 new chars ===")
        
        if len(self.all_chars) < 101:
            self.skipTest("Need at least 101 characters for this test")
            
        new_chars = self.all_chars[51:101]  # 50 characters starting from index 51
        start_char = self.all_chars[10]
        
        print(f"Input - New chars: {len(new_chars)} chars from indices 51-100")
        print(f"Input - Start char: '{start_char}'")
        
        result = select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Result length: {len(result)}")
        print(f"Should be only new chars, no old chars")
        
        # Should return exactly the 50 new characters
        self.assertEqual(len(result), 50)
        self.assertEqual(result, list(new_chars))
    
    def test_complex_scenario(self):
        """Test the specific example from requirements"""
        print(f"\n=== Test: Requirements example scenario ===")
        
        if len(self.all_chars) < 70:
            self.skipTest("Need at least 70 characters for this test")
            
        # Create scenario: new chars at unique indices > 50
        # Use characters that don't have duplicates: 男(52), 父(54), 师(65), 学(66), 医(68)
        new_char_indices = [52, 54, 65, 66, 68]
        if max(new_char_indices) >= len(self.all_chars):
            self.skipTest(f"Need at least {max(new_char_indices)+1} characters")
            
        new_chars = ''.join([self.all_chars[i] for i in new_char_indices])
        start_char = self.all_chars[10]
        
        print(f"Input - New chars: '{new_chars}' (indices: {new_char_indices})")
        print(f"Input - Start char: '{start_char}' (index: 10)")
        print(f"Need {50 - len(new_chars)} old characters")
        print(f"Expected: count back from 10: 10,9,8,7,6,5,4,3,2,1,0")
        print(f"Then continue from end, skipping new char indices: {new_char_indices}")
        
        result = select_characters(new_chars, start_char, self.all_chars)
        
        print(f"Result length: {len(result)}")
        print(f"New chars: {result[:len(new_chars)]}")
        
        old_chars = result[len(new_chars):]
        old_indices = [self.all_chars.index(char) for char in old_chars]
        print(f"Old char indices (first 20): {old_indices[:20]}")
        print(f"Old char indices (last 10): {old_indices[-10:]}")
        
        # Verify correctness
        self.assertEqual(len(result), 50)
        self.assertEqual(len(set(result)), 50, "Result contains duplicates")
        
        # First old char should be from index 10
        self.assertEqual(old_chars[0], self.all_chars[10])
        
        # Verify no new char indices in old chars
        for idx in old_indices:
            self.assertNotIn(idx, new_char_indices, f"Found new char index {idx} in old chars")


if __name__ == '__main__':
    unittest.main(verbosity=2)