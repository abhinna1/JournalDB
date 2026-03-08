import unittest
import tempfile
from pathlib import Path

from fts import FTSIndex
from journal_db.errors import CorruptIndexError

class TestFTSIndex(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal_dir = Path(self.tmp.name)
        self.fts = FTSIndex(self.journal_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_tokenize_lowercases_and_strips_punctuation(self):
        text = "Hello! This is a TEST... of the token-izer."
        tokens = self.fts._tokenize(text)
        
        self.assertIn("hello", tokens)
        self.assertIn("test", tokens)
        self.assertIn("token", tokens)
        self.assertIn("izer", tokens)
        
        # Punctuation should be gone
        self.assertNotIn("hello!", tokens)
        self.assertNotIn("test...", tokens)

    def test_tokenize_removes_stop_words(self):
        text = "a the an and is in to of for with"
        tokens = self.fts._tokenize(text)
        self.assertEqual(len(tokens), 0)

    def test_update_adds_entry_to_index(self):
        self.fts.update("entry_1", "python coding")
        
        # Check in-memory index
        self.assertIn("python", self.fts._index)
        self.assertIn("entry_1", self.fts._index["python"])
        
        self.assertIn("coding", self.fts._index)
        self.assertIn("entry_1", self.fts._index["coding"])

    def test_update_replaces_old_tokens(self):
        self.fts.update("entry_1", "apple banana")
        self.assertIn("apple", self.fts._index)
        
        # Update same entry with new text
        self.fts.update("entry_1", "cherry date")
        
        # Old tokens should be gone
        self.assertNotIn("apple", self.fts._index)
        self.assertNotIn("banana", self.fts._index)
        
        # New tokens should be present
        self.assertIn("cherry", self.fts._index)
        self.assertIn("date", self.fts._index)

    def test_remove_deletes_entry(self):
        self.fts.update("entry_1", "unique_word shared_word")
        self.fts.update("entry_2", "shared_word")
        
        self.fts.remove("entry_1")
        
        # unique_word should be entirely removed from the index structure
        self.assertNotIn("unique_word", self.fts._index)
        
        # shared_word should still exist, but only contain entry_2
        self.assertIn("shared_word", self.fts._index)
        self.assertNotIn("entry_1", self.fts._index["shared_word"])
        self.assertIn("entry_2", self.fts._index["shared_word"])

    def test_search_single_word(self):
        self.fts.update("entry_1", "python is great")
        self.fts.update("entry_2", "i love python")
        self.fts.update("entry_3", "javascript is okay")
        
        results = self.fts.search("python")
        self.assertEqual(results, {"entry_1", "entry_2"})

    def test_search_multiple_words_intersection(self):
        self.fts.update("entry_1", "meeting went sideways today")
        self.fts.update("entry_2", "great meeting today we wrote python")
        self.fts.update("entry_3", "wrote some code today")
        
        results = self.fts.search("meeting python")
        
        # Must contain BOTH words (AND semantics)
        self.assertEqual(results, {"entry_2"})

    def test_search_no_results(self):
        self.fts.update("entry_1", "python coding")
        
        results = self.fts.search("javascript")
        self.assertEqual(len(results), 0)

    def test_search_handles_stop_words_in_query(self):
        self.fts.update("entry_1", "python coding")
        
        # "the" and "is" are stripped, so this searches for "python"
        results = self.fts.search("the python is")
        self.assertEqual(results, {"entry_1"})

    def test_search_empty_query(self):
        self.fts.update("entry_1", "python coding")
        
        # Empty after stripping stop words
        results = self.fts.search("the is and")
        self.assertEqual(len(results), 0)
        
        # Literally empty
        results = self.fts.search("")
        self.assertEqual(len(results), 0)

    def test_persistence(self):
        self.fts.update("entry_1", "python coding")
        
        # Create a new instance pointing to the same directory
        # It should load the index from disk during __init__
        fts2 = FTSIndex(self.journal_dir)
        
        self.assertIn("python", fts2._index)
        self.assertIn("entry_1", fts2._index["python"])

    def test_corrupt_index_raises(self):
        # Write garbage to the index file
        (self.journal_dir / ".journal_fts").write_text("not real json")
        
        with self.assertRaises(CorruptIndexError):
            FTSIndex(self.journal_dir)

if __name__ == "__main__":
    unittest.main()
