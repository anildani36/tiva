import logging

from fastapi import APIRouter
from starlette import status
from starlette.responses import JSONResponse

api_router = APIRouter()
logger = logging.getLogger(__name__)

actuator_api_router = APIRouter(tags=["Actuator API"])


@actuator_api_router.get('/health')
async def health_check():
    logger.info("Health check initiated")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Notification service is up and running"},
    )
