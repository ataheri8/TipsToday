import asyncio
import functools
from asyncio import Future


def run_in_executor(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, lambda: f(*args, **kwargs))

    return inner


def run_async(f, *args):
    loop = asyncio.get_running_loop()
    return loop.call_soon(f, *args)


def as_future(result):
    f = Future()
    f.set_result(result)
    return f
