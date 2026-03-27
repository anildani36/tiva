import logging
from typing import Optional, Annotated

from fastapi import APIRouter, Body
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.enums.notification_type_enum import NotificationType
from src.model import EmailNotification, TeamsNotification

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    EMAIL = 'email'
    TEAMS = 'teams'

notification_api_router = APIRouter(tags=["Notification API"])

@notification_api_router.post('/notify')
async def notify(
    request: Body(Annotated[EmailNotification, TeamsNotification]),
    type: Optional[NotificationType] = NotificationType.EMAIL,
):
    return JSONResponse({'type': type.value})
