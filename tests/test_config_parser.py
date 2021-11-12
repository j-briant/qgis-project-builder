import unittest
from config_parser import load_config


class TestLoading(unittest.TestCase):
    def test_output_is_dict(self):
        self.assertEqual(type(load_config('./test_data/test_yaml.yml')), dict)

    def test_accessing_value(self):
        dy = load_config('./test_data/test_yaml.yml')
        self.assertEqual(dy['name']['family'], 'Smith')
        self.assertEqual(dy['name']['age'], 25)
        self.assertEqual(dy['name']['a']['very']['nested']['value'], ['tada'])

    def test_fails_on_bad_path(self):
        with self.assertRaises(FileNotFoundError):
            load_config('a-very_b@d-path/conf.conf')


if __name__ == '__main__':
    unittest.main()
