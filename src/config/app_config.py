import os
import pathlib
from functools import lru_cache
from typing import List

from jeeva.core.config.base import BaseAppConfig
from pydantic import validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.secrets_manager_service import AWSSecretsManagerService
from src.constants.aws_secrets_service_key_names import AwsSecretsServiceKeyNames
from src.enums.env_enum import Env

STAGING_CONFIG_FILE = str(pathlib.Path().joinpath('src/.staging.env'))
PRODUCTION_CONFIG_FILE = str(pathlib.Path().joinpath('src/.production.env'))


class AppConfig(BaseAppConfig):
    port: int
    cognito_user_pool_id: str
    aws_access_key_id: str = None
    aws_secret_access_key: str = None
    http_requests_read_timeout_in_seconds: int

    model_config = SettingsConfigDict(
        env_file=PRODUCTION_CONFIG_FILE if os.getenv('ENV_NAME') == 'prod' else STAGING_CONFIG_FILE,
        extra='ignore'  # Allow extra fields in env file
    )


    @validator('aws_access_key_id', pre=True, always=True)
    def _set_aws_access_key_id(cls, v, values):
        return AWSSecretsManagerService.get_secret(
            AwsSecretsServiceKeyNames.get_aws_access_key_id_name(values['env_name'].value)
        )

    @validator('aws_secret_access_key', pre=True, always=True)
    def _set_aws_secret_access_key(cls, v, values):
        return AWSSecretsManagerService.get_secret(
            AwsSecretsServiceKeyNames.get_aws_secret_access_key_name(values['env_name'].value)
        )



@lru_cache
def get_configs():
    return AppConfig()