"""
test_parser.py — Unit tests for journal_db.parser (MetaDataParser)

All tests operate on raw strings — no disk I/O needed.
"""

import unittest

from journal_db.parser import parse
from journal_db.schema import MetaDataSchema
from journal_db.errors import ParseError


VALID_ENTRY = """\
---
title: A good day
date: 2026-03-07
tags: [work, reflection]
mood: calm
location: home
---
Today I worked on implementing parser and validator for JournalDB.
I feel motivated.
"""


class TestParseValidEntry(unittest.TestCase):

    def setUp(self):
        self.result = parse(VALID_ENTRY)

    def test_returns_metadata_schema(self):
        self.assertIsInstance(self.result, MetaDataSchema)

    def test_front_matter_title(self):
        self.assertEqual(self.result.title, "A good day")

    def test_front_matter_date(self):
        self.assertIsNotNone(self.result.date)

    def test_front_matter_tags(self):
        self.assertEqual(self.result.tags, ["work", "reflection"])

    def test_front_matter_mood(self):
        self.assertEqual(self.result.mood, "calm")

    def test_front_matter_location(self):
        self.assertEqual(self.result.location, "home")

    def test_body_text(self):
        self.assertIn("implementing parser and validator", self.result.body)
        self.assertIn("motivated", self.result.body)

    def test_body_is_stripped(self):
        self.assertEqual(self.result.body, self.result.body.strip())


class TestParseMissingDelimiters(unittest.TestCase):

    def test_no_delimiters_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse("title: No delimiters here\nJust some text.")

    def test_only_one_delimiter_raises_parse_error(self):
        """Missing closing delimiter."""
        with self.assertRaises(ParseError):
            parse("---\ntitle: Only opening\nNo closing delimiter.")

    def test_empty_string_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse("")


class TestParseInvalidYAML(unittest.TestCase):

    def test_invalid_yaml_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse("---\ntitle: [unclosed bracket\n---\nBody text.")


class TestParseEdgeCases(unittest.TestCase):

    def test_body_with_extra_dashes_not_split(self):
        content = "---\ntitle: Test\ndate: 2026-01-01\n---\nLine one.\n---\nLine two."
        result = parse(content)
        self.assertIn("Line one.", result.body)
        self.assertIn("Line two.", result.body)

    def test_body_whitespace_stripped(self):
        content = "---\ntitle: Test\ndate: 2026-01-01\n---\n\n\n  Hello world.  \n\n"
        result = parse(content)
        self.assertEqual(result.body, "Hello world.")


if __name__ == "__main__":
    unittest.main()
