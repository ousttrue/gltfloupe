import unittest
import ctypes


class TestMemoryView(unittest.TestCase):

    def test_primitive(self):
        values = memoryview((ctypes.c_int * 4)(*range(4)))
        span = values[2:]

        self.assertIsInstance(span, memoryview)
        self.assertEqual(2, len(span))
