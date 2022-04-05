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