import os
import unittest
import tempfile
from mchatserver import parse_config


class TestParseConfig(unittest.TestCase):
    def setUp(self):
        self.test_config = tempfile.NamedTemporaryFile(delete=False)

    def tearDown(self):
        os.unlink(self.test_config.name)

    def test_parse_config_invalid_channel_nos(self):
        with open(self.test_config.name, 'w') as f:
            f.write('channel abc 8000 5\n')
            f.write('channel def 8001 3\n')

        with self.assertRaises(SystemExit):
            parse_config(self.test_config.name)

    def test_parse_config_valid_channel_nos(self):
        with open(self.test_config.name, 'w') as f:
            f.write('channel abc 8000 5\n')
        
        expected_output = [
            ('abc', 8000, 5),
        ]
        self.assertEqual(parse_config(self.test_config.name), expected_output)
    
    def test_parse_config_invalid_entry(self):
        with open(self.test_config.name, 'w') as f:
            f.write('channel abc 8000\n')

        with self.assertRaises(SystemExit):
            parse_config(self.test_config.name)
    
    def test_parse_config_invalid_channel_name(self):
        with open(self.test_config.name, 'w') as f:
            f.write('channel channel2 8000 3\n')  # Invalid channel name

        with self.assertRaises(SystemExit):
            parse_config(self.test_config.name)

    def test_parse_config_invalid_duplicate_port(self):
        with open(self.test_config.name, 'w') as f:
            f.write('channel abc 8000 5\n')
            f.write('channel def 9000 5\n')
            f.write('channel xyz 8000 3\n')  # Duplicate port

        with self.assertRaises(SystemExit):
            parse_config(self.test_config.name)
    
    def test_parse_config_invalid_duplicate_name(self):
        with open(self.test_config.name, 'w') as f:
            f.write('channel abc 8000 5\n')
            f.write('channel abc 9000 4\n')
            f.write('channel xyz 9001 3\n')  # Duplicate name

        with self.assertRaises(SystemExit):
            parse_config(self.test_config.name)
    
    def test_parse_config_invalid_capacity(self):
        with open(self.test_config.name, 'w') as f:
            f.write('channel channel 8000 6\n')  # Invalid capacity

        with self.assertRaises(SystemExit):
            parse_config(self.test_config.name)

if __name__ == '__main__':
    unittest.main()
