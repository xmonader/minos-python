"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""

import unittest

from minos.common import (
    Response,
)
from tests.aggregate_classes import (
    Car,
)


class TestSomething(unittest.TestCase):
    def setUp(self) -> None:
        self.items = [Car(1, 1, 3, "blue"), Car(2, 1, 5, "red")]

    async def test_content(self):
        response = Response(self.items)
        self.assertEqual(self.items, await response.content())

    async def test_content_single(self):
        response = Response(self.items[0])
        self.assertEqual([self.items[0]], await response.content())

    async def test_raw_content(self):
        response = Response(self.items)
        self.assertEqual([item.avro_data for item in self.items], await response.raw_content())

    async def test_raw_content_single(self):
        response = Response(self.items[0])
        self.assertEqual([self.items[0].avro_data], await response.raw_content())


if __name__ == "__main__":
    unittest.main()
