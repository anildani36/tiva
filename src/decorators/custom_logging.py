import inspect
import logging
from functools import wraps

from starlette.requests import Request

from src.api.crm_base_api_service import CRMBaseAPIService

logger = logging.getLogger(__name__)


def custom_logging(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        # user_id = kwargs.get('user_id', '')
        params = kwargs if kwargs else args
        logger.info(f"Entering: {function_name} - params={params}")
        try:
            response = func(*args, **kwargs)
            logger.info(f"Exiting: {function_name}")
            return response
        except Exception as e:
            logger.exception(f"Exception in {function_name}: {e}")
            raise
    return wrapper

def async_custom_logging(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        function_name = func.__name__
        params = kwargs if kwargs else args
        if 'request' in params and isinstance(params['request'], Request):
            user_id = params['request'].state.base_api.user_id
        elif 'base_api' in params and isinstance(params['base_api'], CRMBaseAPIService):
            user_id = params['base_api'].user_id
        elif params and isinstance(params, tuple) and isinstance(params[0], CRMBaseAPIService):
            user_id = params[0].user_id
        else:
            user_id = None
        logger.info(f"Entering {function_name} {f'for user: {user_id}' if user_id else ''}")
        try:
            response = await func(*args, **kwargs)
            logger.info(f"Exiting {function_name} {f'for user: {user_id}' if user_id else ''}")
            return response
        except Exception as e:
            logger.exception(f"Exception in {function_name} {f'for user: {user_id}' if user_id else ''}")
            raise
    return wrapper