#!/usr/bin/env python3
from typing import List

import aws_cdk as cdk
import boto3

from cdk_stack import IntegrationPlatformCloudFormationAppStack

app = cdk.App()

COGNITO_USER_POOL_ID_STAGING: str = "us-east-1_kAkBYrvkt"
COGNITO_USER_POOL_ID_PRODUCTION: str = "us-east-1_VexGF7uyH"


def get_user_pool_client_ids(user_pool_id: str) -> List[str]:
    cognito_client = boto3.client('cognito-idp')
    response = cognito_client.list_user_pool_clients(
        UserPoolId=user_pool_id
    )
    client_ids = [user_pool_client['ClientId'] for user_pool_client in response['UserPoolClients']]
    print('UserPool Client IDs :: ', client_ids)
    return client_ids


IntegrationPlatformCloudFormationAppStack(app, "IntegrationPlatformCloudFormationAppStack-Staging",
                                          env=cdk.Environment(
                                              account="712004218608",
                                              region="us-east-1",
                                          ),
                                          environment="staging",
                                          cognito_user_pool_id=COGNITO_USER_POOL_ID_STAGING,
                                          cidr="10.1.0.0/16",
                                          vpc_id="vpc-00fdd01d62b4a9ac2",
                                          cognito_user_pool_client_ids=get_user_pool_client_ids(
                                              COGNITO_USER_POOL_ID_STAGING),
                                          codeartifact_token=app.node.try_get_context('codeartifact-token')
                                          )

IntegrationPlatformCloudFormationAppStack(app, "IntegrationPlatformCloudFormationAppStack-Prod",
                                          env=cdk.Environment(
                                              account="712004218608",
                                              region="us-east-1",
                                          ),
                                          environment="prod",
                                          cognito_user_pool_id=COGNITO_USER_POOL_ID_PRODUCTION,
                                          cidr="10.2.0.0/16",
                                          vpc_id="vpc-09ee0099125c3019d",
                                          cognito_user_pool_client_ids=get_user_pool_client_ids(
                                              COGNITO_USER_POOL_ID_PRODUCTION),
                                          codeartifact_token=app.node.try_get_context('codeartifact-token')
                                          )

app.synth()
