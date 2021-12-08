import unittest
from gltfloupe.jsonutil import to_pretty


class TestJsonToString(unittest.TestCase):

    def test_primitive(self):
        self.assertEqual('1', to_pretty(1))
        self.assertEqual('1.0', to_pretty(1.0))
        self.assertEqual('"abc"', to_pretty("abc"))
        self.assertEqual('null', to_pretty(None))
        self.assertEqual('true', to_pretty(True))
        self.assertEqual('false', to_pretty(False))

    def test_array(self):
        self.assertEqual('[]', to_pretty([]))
        ab = '''
[
  "a",
  "b",
  "c"
]'''.strip()
        self.assertEqual(ab, to_pretty(['a', 'b', 'c']))

    def test_dict(self):
        ab = '''
{
  "a": "b"
}'''.strip()
        self.assertEqual(ab, to_pretty({'a': 'b'}))

        abcd = '''
{
  "a": "b",
  "c": "d"
}'''.strip()
        self.assertEqual(abcd, to_pretty({'a': 'b', 'c': 'd'}))


if __name__ == '__main__':
    unittest.main()
