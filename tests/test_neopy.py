from unittest import TestCase

from neopy.examples import examples


class MainTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_example1(self):
        for k, e in examples.items():
            result = e()
            print(result)
