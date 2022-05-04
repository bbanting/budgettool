import unittest
from datetime import datetime

from entry import Entry, cents_to_dollars, dollars_to_cents


def make_entry(id=1, date=datetime.today(), amount=5000, tags=None, note="This is a note"):
    if not tags:
        tags = ["other"]
    return Entry(id, date, amount, tags, note)


class TestEntry(unittest.TestCase):

    def test_to_tuple(self):
        entry = make_entry()
        date = entry.date.strftime("%Y/%m/%d")
        self.assertEqual(entry.to_tuple(), (1, date, 5000, "other", "This is a note"))

    def test_from_tuple(self):
        entry1 = Entry(4, datetime(2022, 3, 28), 5000, ["other"], "Here's a note")
        data = (4, "2022/03/28", 5000, "other", "Here's a note")
        entry2 = Entry.from_tuple(data)
        self.assertEqual(entry1, entry2)

    def test_category_expense(self):
        entry = make_entry(amount=-5000)
        self.assertEqual(entry.category, "expense")

    def test_category_income(self):
        entry = make_entry(amount=5000)
        self.assertEqual(entry.category, "income")


class TestAmountConvert(unittest.TestCase):
    def test_in_dollars_positive(self):
        entry = make_entry(amount=5000)
        self.assertEqual(entry.dollar_str(), "+$50.00")

    def test_in_dollars_negative(self):
        entry = make_entry(amount=-700)
        self.assertEqual(entry.dollar_str(), "-$7.00")

    def test_cents_to_dollars(self):
        self.assertEqual(cents_to_dollars(7050), 70.50)

    def test_dollars_to_cents_positive(self):
        self.assertEqual(dollars_to_cents("50"), 5000)

    def test_dollars_to_cents_negative(self):
        self.assertEqual(dollars_to_cents("-7"), -700)



if __name__ == "__main__":
    unittest.main()