import unittest

from tests import async_test
from toutiao.crawl.login import LoginPage


class TestLogin(unittest.TestCase):
    async def asyncSetUp(self):
        pass

    @async_test
    async def test_login(self):
        tt = LoginPage()
        image = await tt.login()
        with open("/tmp/tt.png", "wb") as f:
            image.save(f)
        await tt.stop()
