from django.test import SimpleTestCase

from app.calc import add, subtract


class Test(SimpleTestCase):
    def test_add(self):
        self.assertEqual(add(3, 4), 7)

    def test_subtract(self):
        self.assertEqual(subtract(2, 4), -2)
