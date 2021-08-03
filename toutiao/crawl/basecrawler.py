import asyncio
import base64
import logging
import os
from datetime import tzinfo
from io import BytesIO
from typing import Any, Awaitable, Callable, List, Tuple, Union

import arrow
import pyppeteer as pp
from PIL import Image
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Response
from pyppeteer.page import Page, PageError

logger = logging.getLogger(__name__)


class ResponseInterceptor:
    """
    传入response处理回调函数(awaiable)和一个buffer。其中buffer[0]为`event`对象，buffer[1]则存放处理repsone得到的`result`。

    通过`event.set`来通知等待者已经获取到对应的response。

    Examples:

    >>> async def on_response(resp):
    ...     if resp.request.url == "...":
    ...         return await resp.buffer()

    >>> await crawler.goto(url, on_response, "test")
    >>> data = await crawler.wait_for("test", 2)
    """

    def __init__(self, handler: Callable[[int], Awaitable], buffer: List):
        self.handler = handler
        self.buffer = buffer

    async def handle_response(self, resp: Response):
        result = await self.handler(resp)
        if result is not None:
            self.buffer[1] = result
            self.buffer[0].set()


class BaseCrawler:
    def __init__(self, base_url: str, screenshot_dir: str = None):
        self._browser: Browser = None
        self._base_url = base_url

        self._screenshot_dir = screenshot_dir

        # event_name -> (Event, data)
        self._events = {}

        preload = os.path.join(os.path.dirname(__file__), "preload.js")
        with open(preload, "r") as f:
            self._preload_script = f.read()

    @property
    def base_url(self):
        return self._base_url

    @property
    def screenshot_dir(self):
        return self._screenshot_dir

    async def start(self):
        if self._browser is None:
            args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certifcate-errors",
                "--ignore-certifcate-errors-spki-list",
                '--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3312.0 Safari/537.36"',
            ]
            self._browser = await pp.launch(
                {"headless": True, "args": args, "ignoreHTTPSErrors": True}
            )

    async def stop(self):
        await self._browser.close()

    async def goto(
        self,
        url: str,
        interceptor: Callable[[int], Awaitable] = None,
        name: str = None,
    ) -> Tuple[Page, Response]:
        """获取url指定的页面，返回Page对象和Response。

        本函数返回的`response`直接对应于url。当获取到`url`指定的页面后，可能触发其它网络请求（比如js, ajax等），如果要获取这些网络请求的数据，需要通过`interceptor`机制。

        如果需要同步获取该页面触发的其它请求中的某个`response`，请指定`name`值，后续可以使用`crawler.wait_response(name)`来得到等待中的`response`的经处理后的数据。如果只允许异步获取某个`response`中的数据，则可以不传入`name`。此时`interceptor`需要自行保存（或者使用）处理后的数据。

        Args:
            url (str): [description]
            interceptor (Callable[[int], Awaitable], optional): [description]. Defaults to None.
            name (str, optional): [description]. Defaults to None.

        Returns:
            Tuple[Page, Response]: [description]
        """
        if not url.startswith("http"):
            # url is just a server path, not a full url
            url = f"{self._base_url}/{url}"

        page: Page = await self._browser.newPage()
        await page.evaluateOnNewDocument(self._preload_script)

        if interceptor:
            if name:
                buffer = [asyncio.Event(), None]
                self._events[name] = buffer
                ri = ResponseInterceptor(interceptor, buffer)
                page.on("response", ri.handle_response)
            else:
                page.on("response", interceptor)

        resp: pp.network_manager.Response = await page.goto(url)

        logger.debug("page %s returns %s", page.url, resp.status)
        return page, resp

    async def wait_response(self, name: str, timeout: int = 10):
        """等待命名为`name`的某个网络请求的`response`处理结果。

        Args:
            name (str): [description]
            timeout (int, optional): [description]. Defaults to 10.

        Raises:
            ValueError: [description]

        Returns:
            [type]: [description]
        """
        try:
            logger.info("waiting for repsone: %s", name)
            buffer = self._events.get(name)
            event = buffer[0]
            if event is None:
                raise ValueError(f"Event({name}) not exist")

            await asyncio.wait_for(event.wait(), timeout)

            logger.info("Got response named as %s, len is %s", name, len(buffer[1]))

            return buffer[1]
        finally:
            if name in self._events:
                del self._events[name]

    async def select_from_dropdown(self, page: Page, control: str, option: str):
        """模拟dropdown的选择操作。

        一些页面的下拉菜单（select控件）是经过包装的，不能直接使用page.select()来完成选择，需要使用模拟操作的方法。

        Args:
            page (Page): the page object
            control (str): selector for the control, for example, `div.select_box>ul>li[data-value='x']`
            option (str): selector for the option
        """
        await page.Jeval(control, "el => el.click()")
        await page.waitFor(100)
        await page.screenshot(path="/root/trader/screenshot/select_1.jpg")
        await page.Jeval(option, "el => el.click()")
        await page.screenshot(path="/root/trader/screenshot/select_2.jpg")

    def error_time(self):
        n = arrow.now()
        return f"{n.year:02d}{n.month:02d}{n.day:02d}-{n.hour:02d}{n.minute:02d}"

    async def screenshot(self, page: Page, filename: str = None):
        if filename is None:
            path = page.url.split("/")[-1].split("?")[0]
            filename = f"{path}-{self.error_time()}.png"

        logger.info("screenshot <%s> for page: %s", filename, page.url)

        if self.screenshot_dir:
            await page.screenshot(path=os.path.join(self.screenshot_dir, filename))
            content_file = f"{path}-{self.error_time()}.html"
            with open(os.path.join(self.screenshot_dir, content_file), "w") as f:
                f.write(await page.content())

    async def get_img_by_data_url(self, page: Page, selector: str):
        """从`selector`指定的元素中的data-url获取image binary data

        `selector`应该能直接定位到包含`src`属性的元素
        """
        data_url = await page.Jeval(selector, "el => el.getAttribute('src')")
        if not (data_url and data_url.startswith("data:image/")):
            raise ValueError(f"Can't find img by selector: {selector}")

        # get format from data-url: data:image/png;base64,iVBORw0KGgoAAAANSUh...
        meta, data = data_url.split(",")
        format, enc = meta.split("/")[-1].split(";")

        if enc != "base64":
            raise ValueError(f"Unsupported image format: {enc}")

        buffer = BytesIO(base64.b64decode(data))
        img = Image.open(buffer)

        return img

    async def click(
        self,
        page: Page,
        selector: str,
        visible=False,
        hidden=False,
        timeout: int = 10 * 1000,
    ):
        """combine `waitFor` and `click`

        if selector starts with "//", then it's treated as xpath

        Args:
            page (Page): [description]
            selector (str): [description]
            visible: params required by waitForXpath/waitForSelector
        """
        elements = None
        if selector.startswith("//"):
            elements = await page.waitForXPath(
                selector, visible=visible, hidden=hidden, timeout=timeout
            )
        else:
            elements = await page.waitForSelector(
                selector, visible=visible, hidden=hidden, timeout=timeout
            )

        if elements is None or len(elements) == 0:
            raise PageError(message=f"failed to locate element by {selector}")

        if isinstance(elements, list):
            await elements[0].click()
        else:
            await elements.click()
