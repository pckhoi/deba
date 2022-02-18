import random, time
from typing import TypeVar, Callable

T = TypeVar("T")


def retry_with_backoff(fn: Callable[[], T], retries=5, backoff_in_seconds=1) -> T:
    x = 0
    while True:
        try:
            return fn()
        except:
            if x == retries:
                raise
            else:
                sleep = backoff_in_seconds * 2 ** x + random.uniform(0, 1)
                print("    backoff for %f seconds" % sleep)
                time.sleep(sleep)
                x += 1
