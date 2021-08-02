import asyncio
from asyncio.log import logger
import os
from typing import List

import pyppeteer
from pyppeteer import errors

from toutiao.crawl.basecrawler import BaseCrawler
from toutiao.crawl.selectors import Selectors
import logging

logger = logging.getLogger(__name__)


class ToutiaoClient(BaseCrawler):
    def __init__(self, screenshot_dir: str = None):
        screenshot_dir = screenshot_dir or os.path.expanduser("~/toutiao/screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        base_url = "https://mp.toutiao.com/"
        super().__init__(base_url, screenshot_dir=screenshot_dir)

        self._login_decay_time = 1.5

    async def start(self, *args, **kwargs):
        await super().start()

        asyncio.create_task(self.login())

    async def login(self):
        page, _ = await self.goto("/auth/page/login")

        try:
            # get image
            image = await self.get_img_by_data_url(page, Selectors.qrcode_login)

            path = os.path.expanduser("~/toutiao/login_qr.png")
            image.save(path)
            print("please open http://server/toutiao to scan QR code to login")

            await page.waitForNavigation()
            if page.url.find("profile_v4") == -1:
                raise errors.NavigationError("login failed due to we're not redirected to right page")

            return True
        except Exception as e:
            self._login_decay_time *= 2
            logger.warning("login failed due to %s, retrying in seconds: %s", str(e), self._login_decay_time)
            
            await self.screenshot(page)
            await asyncio.sleep(self._login_decay_time)
            await self.login()
