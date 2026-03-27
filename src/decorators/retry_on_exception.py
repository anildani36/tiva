from typing import Iterable, Tuple, Type

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt, stop_after_delay, wait_random_exponential
)


def retry_on_exception(
    exc_types: Iterable[Type[Exception]] = (Exception,)
):
    exc_tuple: Tuple[Type[Exception], ...] = tuple(exc_types)
    return retry(
        retry=retry_if_exception_type(exc_tuple),
        wait=wait_random_exponential(multiplier=1.2, min=1, max=10),
        stop=(stop_after_delay(120) | stop_after_attempt(5)),
        reraise=True,
    )