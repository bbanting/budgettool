from datetime import datetime
import unittest
from unittest.mock import patch

import commands
from main import BTError


class TestGetDate(unittest.TestCase):
    def test_get_date_abort(self):
        with patch("commands.input", return_value="q"):
            self.assertRaises(BTError, commands.get_date)
        
    def test_get_date_no_input(self):
        with patch("commands.input", return_value=""):
            ret_val = commands.get_date()
            self.assertEqual(ret_val, commands.TODAY)
            
    def test_get_date_not_enough_input(self):
        with patch("commands.input", return_value="jan"):
            ret_val = commands.get_date()
            self.assertEqual(ret_val, None)

    def test_get_date_too_much_input(self):
        with patch("commands.input", return_value="jan 15 1958 hi"):
            ret_val = commands.get_date()
            self.assertEqual(ret_val, None)
    
    def test_get_date_success_two(self):
        with patch("commands.input", return_value="jan 15"):
            ret_val = commands.get_date()
            self.assertEqual(ret_val, datetime(commands.TODAY.year, 1, 15))

    def test_get_date_success_three(self):
        with patch("commands.input", return_value="jan 15 2020"):
            ret_val = commands.get_date()
            self.assertEqual(ret_val, datetime(2020, 1, 15))


class TestGetAmount(unittest.TestCase):
    def test_get_amount_abort(self):
        with patch("commands.input", return_value="q"):
            self.assertRaises(BTError, commands.get_date)
    
    def test_get_amount_no_sign(self):
        with patch("commands.input", return_value="45"):
            self.assertIsNone(commands.get_amount())
    
    def test_get_amount_positive(self):
        with patch("commands.input", return_value="+45"):
            ret_val = commands.get_amount()
            self.assertEqual(ret_val, 4500)

    def test_get_amount_positive(self):
        with patch("commands.input", return_value="-45"):
            ret_val = commands.get_amount()
            self.assertEqual(ret_val, -4500)


class TestGetTags(unittest.TestCase):
    def test_get_tags_abort(self):
        with patch("commands.input", return_value="q"):
            self.assertRaises(BTError, commands.get_tags)

    def test_get_tags_help(self):
        with patch("commands.input", return_value="help"):
            self.assertIsNone(commands.get_tags())

    @patch("config.udata.tags", ["food", "other"])
    def test_get_tags_invalid(self):
        with patch("commands.input", return_value="lamps paper"):
            self.assertIsNone(commands.get_tags())

    @patch("config.udata.tags", ["food", "other"])
    def test_get_tags_valid(self):
        with patch("commands.input", return_value="other"):
            ret_val = commands.get_tags()
            self.assertEqual(ret_val, ["other"])
    

class TestGetNote(unittest.TestCase):
    def test_get_note_about(self):
        with patch("commands.input", return_value="q"):
            self.assertRaises(BTError, commands.get_tags)
    
    def test_get_note_empty(self):
        with patch("commands.input", return_value=""):
            self.assertEqual(commands.get_note(), "...")
    
    def test_get_note_success(self):
        with patch("commands.input", return_value="Example note!"):
            self.assertEqual(commands.get_note(), "Example note!")
            