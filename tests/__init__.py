"""Unit test package for toutiao."""

import asyncio
from functools import wraps


def async_test(func):
    async def init_and_run(self, *args, **kwargs):
        if getattr(self, "asyncSetUp", None):
            await self.asyncSetUp()

        await func(self, *args, **kwargs)

        if getattr(self, "asyncTearDown", None):
            await self.asyncTearDown()

    @wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.run(init_and_run(*args, **kwargs))

    return wrapper
