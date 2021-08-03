import logging
import unittest

import pyppeteer
from tests import async_test
from toutiao.client import ToutiaoClient


class TestToutiaoClient(unittest.TestCase):
    async def asyncSetUp(self):
        pass

    @async_test
    async def test_start(self):
        tt = ToutiaoClient()
        self.assertTrue(await tt.start())
        await tt.stop()

    @async_test
    async def test_post_wtt(self):
        pyppeteer.DEBUG = True
        tt = ToutiaoClient()
        await tt.start()
        await tt.online()

        pics = ["/tmp/tt.png"]
        await tt.post_weitoutiao("hello", pics)
