import os

import timg

from toutiao.crawl.basecrawler import BaseCrawler
from toutiao.crawl.selectors import Selectors


class LoginPage(BaseCrawler):
    def __init__(self, screenshot_dir: str = None):
        screenshot_dir = screenshot_dir or os.path.expanduser("~/toutiao/screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        base_url = "https://mp.toutiao.com/"
        super().__init__(base_url, screenshot_dir=screenshot_dir)

    async def login(self):
        await self.start()
        page, _ = await self.goto("/auth/page/login")

        # get image
        image = await self.get_img_by_data_url(page, Selectors.qrcode_login)
        print("please scan the following QR using your phone to login")

        image.show()
        # render = timg.Renderer()
        # render.load_image(image)
        # render.resize(60)
        # render.grayscale()
        # render.render(timg.Ansi24FblockMethod)
        return image
