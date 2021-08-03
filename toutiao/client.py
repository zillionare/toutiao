import asyncio
import logging
import os
from typing import List

from pyppeteer import errors

from toutiao.crawl.basecrawler import BaseCrawler
from toutiao.crawl.controls import Button, Input, Link
from toutiao.crawl.selectors import Selectors

logger = logging.getLogger(__name__)


class ToutiaoClient(BaseCrawler):
    def __init__(self, screenshot_dir: str = None):
        screenshot_dir = screenshot_dir or os.path.expanduser("~/toutiao/screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        base_url = "https://mp.toutiao.com/"
        super().__init__(base_url, screenshot_dir=screenshot_dir)

        self._login_decay_time = 1.5
        self._login_success_event = asyncio.Event()
        self._online = False

    async def start(self, *args, **kwargs):
        await super().start()

        asyncio.create_task(self.login())

    async def online(self):
        if self._online:
            return
        else:
            await self._login_success_event.wait()
            self._online = True

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
                raise errors.NavigationError(
                    "login failed due to we're not redirected to right page"
                )

            logger.info("login succeed")
            self._online = True
            self._login_success_event.set()

            return True
        except Exception as e:
            self._login_decay_time *= 2
            logger.warning(
                "login failed due to %s, retrying in seconds: %s",
                str(e),
                self._login_decay_time,
            )

            await self.screenshot(page)
            await asyncio.sleep(self._login_decay_time)
            await self.login()

    async def post_article(self, doc):
        pass

    async def post_weitoutiao(self, text: str, pics: List[str], topic: str = None):
        page, _ = await self.goto("profile_v4/weitoutiao/publish")

        try:
            # 打开图片上传对话框，如果pics存在，则上传图片
            if pics:
                pic_button = await Button("图片").bind(page)
                await pic_button.click()

                # collect pics by input control
                files = await Input("本地上传").bind(page)
                await files.uploadFile(*pics)

                # confirm upload
                confirm_button = await Button("确定").bind(page)
                await confirm_button.click()

            # input text
            edit_box = await page.querySelector("div.syl-editor div.ProseMirror")
            html = self._format_paragraph(text)
            await edit_box.Jeval(".", f"el->el.innerHTML={html}")

            # 发布
            publish_button = await Button("发布").bind(page)
            await publish_button.click()
        except Exception as e:
            logger.warning(str(e))
            await self.screenshot(page)

    def _format_paragraph(self, text):
        """convert plain text to html paragraph

        Args:
            text ([type]): [description]
        """
        paras = text.split("\n")
        html = [f"<p>{para}</p>" for para in paras]
        return "".join(html)
