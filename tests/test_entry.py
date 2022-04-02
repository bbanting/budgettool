import unittest
from datetime import datetime

from entry import Entry, cents_to_dollars, dollars_to_cents


def make_entry():
    return Entry(1, datetime.today(), 5000, ["other"], "This is a note")

class TestEntry(unittest.TestCase):

    def test_to_tuple(self):
        entry = make_entry()
        date = entry.date.strftime("%Y/%m/%d")
        self.assertEqual(entry.to_tuple(), (1, date, 5000, "other", "This is a note"))


class TestAmountConvert(unittest.TestCase):
    def test_cents_to_dollars_positive(self):
        self.assertEqual(cents_to_dollars(5000), "+$50.00")

    def test_cents_to_dollars_negative(self):
        self.assertEqual(cents_to_dollars(-700), "-$7.00")

    def test_dollars_to_cents_positive(self):
        self.assertEqual(dollars_to_cents("50"), 5000)

    def test_dollars_to_cents_negative(self):
        self.assertEqual(dollars_to_cents("-7"), -700)


if __name__ == "__main__":
    unittest.main()