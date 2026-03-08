"""
test_schema.py — Unit tests for MetaDataSchema.from_dict (factory + validation)

All tests pass plain dicts — no parsing or disk I/O needed.
"""

import unittest
from datetime import date

from journal_db.schema import MetaDataSchema
from journal_db.errors import ValidationError


def valid_data(**overrides):
    base = {"title": "A Fine Day", "date": "2026-03-07", "body": "Some content."}
    base.update(overrides)
    return base


class TestFromDictRequiredFields(unittest.TestCase):

    def test_valid_minimal_entry_passes(self):
        result = MetaDataSchema.from_dict(valid_data())
        self.assertIsInstance(result, MetaDataSchema)

    def test_valid_full_entry_passes(self):
        MetaDataSchema.from_dict(valid_data(tags=["work", "life"], mood="happy", location="home"))

    def test_missing_title_raises(self):
        data = valid_data()
        del data["title"]
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(data)

    def test_empty_title_raises(self):
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(valid_data(title=""))

    def test_whitespace_only_title_raises(self):
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(valid_data(title="   "))

    def test_missing_date_raises(self):
        data = valid_data()
        del data["date"]
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(data)

    def test_invalid_date_format_raises(self):
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(valid_data(date="07-03-2026"))

    def test_non_date_string_raises(self):
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(valid_data(date="not-a-date"))

    def test_date_object_is_accepted(self):
        MetaDataSchema.from_dict(valid_data(date=date(2026, 3, 7)))


class TestFromDictOptionalFields(unittest.TestCase):

    def test_tags_as_list_passes(self):
        MetaDataSchema.from_dict(valid_data(tags=["work", "life"]))

    def test_tags_as_string_raises(self):
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(valid_data(tags="work"))

    def test_tags_with_non_string_item_raises(self):
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(valid_data(tags=["work", 42]))

    def test_empty_tags_list_passes(self):
        MetaDataSchema.from_dict(valid_data(tags=[]))

    def test_mood_as_string_passes(self):
        MetaDataSchema.from_dict(valid_data(mood="reflective"))

    def test_mood_as_non_string_raises(self):
        with self.assertRaises(ValidationError):
            MetaDataSchema.from_dict(valid_data(mood=99))

    def test_location_as_string_passes(self):
        MetaDataSchema.from_dict(valid_data(location="café"))

    def test_absent_optional_fields_pass(self):
        MetaDataSchema.from_dict({"title": "Minimal", "date": "2026-01-01", "body": ""})


if __name__ == "__main__":
    unittest.main()
