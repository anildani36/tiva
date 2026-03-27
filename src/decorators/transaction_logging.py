import logging
from functools import wraps

logger = logging.getLogger(__name__)


def transaction_logging(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        params = kwargs if kwargs else args
        logger.info(f"Transaction logging: {function_name} - params={params}")
        try:
            response = func(*args, **kwargs)
            # store integration transactions data
            logger.info(f"Storing integration transaction data")
            logger.info(f"Exiting transaction logging: {function_name}")
            return response
        except Exception as e:
            logger.exception(f"Exception in {function_name}: {e}")
            raise
    return wrapper
