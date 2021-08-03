import pyppeteer
from pyppeteer.element_handle import ElementHandle
from pyppeteer.page import Page, PageError


class Element:
    def __init__(
        self,
        tag: str,
        caption: str = None,
        name: str = None,
        xpath: str = None,
        tooltip: str = None,
    ) -> None:
        """select an element by name, tooltip, caption or xpath

        Args:
            type (str): the type of element
            name (str, optional): the name attribute of the button. Defaults to None.
            caption (str, optional): the title/caption of the button. Defaults to None.
            xpath (str, optional): [description]. Defaults to None.
            tooltip (str, optional): the tooltips of the button. Defaults to None.

        Raises:
            Exception: [description]
        """
        tag = tag.lower()
        self.tag = tag

        if xpath:
            self.xpath = xpath
        elif name:
            self.xpath = f"//{tag}[@name='{name}']"
        elif caption:
            self.xpath = f"//{tag}[contains(. , '{caption}')]"
        elif tooltip:
            self.xpath = f"//{tag}[@title='{tooltip}']"
        else:
            raise Exception("at least one of name, caption and xpath must be set")

    async def bind(self, page: Page, timeout: int = 10) -> ElementHandle:
        """bind the element to the page

        Args:
            page (Page): the page to bind
            timeout (int, optional): the timeout (in seconds) of waiting for element to be found. Defaults to 10.

        """
        await page.waitForXPath(self.xpath, timeout=timeout * 1000)

        el = await page.xpath(self.xpath)
        if el and len(el) == 1:
            return el[0]
        elif el and len(el) > 1:
            raise PageError("more than one button found")
        else:
            return None


class Button(Element):
    def __init__(
        self,
        caption: str = None,
        name: str = None,
        xpath: str = None,
        tooltip: str = None,
    ) -> None:
        """select an button by name, tooltip, caption or xpath"""
        super().__init__("button", caption, name, xpath, tooltip)


class Link(Element):
    def __init__(
        self,
        caption: str = None,
        name: str = None,
        tooltip: str = None,
        xpath: str = None,
    ) -> None:
        """select a link by name, caption, tooltip, or xpath"""
        super().__init__("a", caption, name, xpath, tooltip)


class Input(Element):
    def __init__(
        self,
        caption: str = None,
        name: str = None,
        xpath: str = None,
        tooltip: str = None,
    ) -> None:
        """select an input control by name, caption, tooltip or xpath

        Args:
            caption (str, optional): [description]. Defaults to None.
            name (str, optional): [description]. Defaults to None.
            xpath (str, optional): [description]. Defaults to None.
            tooltip (str, optional): [description]. Defaults to None.
        """
        super().__init__("input")
