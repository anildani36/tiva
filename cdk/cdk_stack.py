import json
import platform

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticache as elasticache,
    aws_ecs_patterns as ecs_patterns,
    aws_apigatewayv2 as apigatewayv2,
    aws_apigatewayv2_integrations as integrations,
    aws_apigatewayv2_authorizers as authorizers,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_logs as logs,
    Duration,
    RemovalPolicy
)
import aws_cdk as cdk
from aws_cdk.aws_elasticloadbalancingv2 import Protocol
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct


class IntegrationPlatformCloudFormationAppStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, *, environment: str, cognito_user_pool_id: str, cidr: str,
                 vpc_id: str, cognito_user_pool_client_ids: list, codeartifact_token: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.codeartifact_token = codeartifact_token

        # Assume existing VPC is available
        self.vpc = ec2.Vpc.from_lookup(self, 'VPC', vpc_id=vpc_id)

        # Define an ECS task definition with a container
        self.fargate_task_definition = self.create_fargate_task_definition()

        self.fargate_container = self.create_fargate_container(environment)

        self.fargate_container.add_environment('ENV_NAME', environment)

        # ECS Cluster
        cluster = ecs.Cluster(self, f'R2D2-Integration-Platform-ECS-Cluster-{environment}', vpc=self.vpc)

        # Create Fargate Service
        self.fargate_service = (
            ecs_patterns.ApplicationLoadBalancedFargateService(self,
                                                               f'R2D2-Integration-Platform-Fargate'
                                                               f'-Service-{environment}',
                                                               cluster=cluster,
                                                               task_definition=self.fargate_task_definition,
                                                               desired_count=1,
                                                               open_listener=False,
                                                               assign_public_ip=False,
                                                               public_load_balancer=False
                                                               ))

        self.fargate_task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                    "cognito-idp:AdminGetUser",
                    "scheduler:*",
                    "iam:PassRole"
                    ],
                resources=["*"]
            )
        )

        # Add SNS publish permissions
        self.fargate_task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'sns:Publish'
                ],
                resources=[f"arn:aws:sns:us-east-1:712004218608:R2D2-Analytics-SNS-Topic-{environment}"]
            )
        )

        # Output the DNS name of the Load Balancer
        cdk.CfnOutput(self, 'LoadBalancerDNS', value=self.fargate_service.load_balancer.load_balancer_dns_name)

        self.fargate_service.service.connections.security_groups[0].add_ingress_rule(
            ec2.Peer.ipv4(cidr),
            ec2.Port.tcp(80),
            f'[R2D2-Integration-Platform] Allow incoming traffic on port 80 from Load Balancer {cidr}'
        )

        self.fargate_service.load_balancer.connections.security_groups[0].add_ingress_rule(
            ec2.Peer.ipv4(cidr),
            ec2.Port.tcp(80),
            f'[R2D2-Integration-Platform] Allow incoming traffic on port 80 from API Gateway {cidr}'
        )

        self.fargate_service.target_group.configure_health_check(
            enabled=True,
            port="3002",
            interval=Duration.seconds(300),
            path="/actuator/health",
            protocol=Protocol.HTTP
        )

        # Elasticache Redis

        redis_logs_group = logs.LogGroup(
            self,
            f"R2D2-Integration-Platform-redis-log-group-{environment}",
            log_group_name=f"R2D2-Integration-Platform-redis-logs-{environment}",
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        redis_security_group = ec2.SecurityGroup(
            self, "R2D2-Integration-Platform-redis-security-group",
            vpc=self.vpc,
            description="Security group for R2D2-Integration-Platform Redis",
            allow_all_outbound=True
        )

        redis_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Allow access from the VPC"
        )

        subnet_group = elasticache.CfnSubnetGroup(self, f'R2D2-Integration-Platform-VPC-Subnet-Group-{environment}',
            description='[R2D2-Integration-Platform] Subnet Group for Redis',
            subnet_ids=self.vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT).subnet_ids
        )

        redis_cluster = elasticache.CfnCacheCluster(self, f'R2D2-Integration-Platform-Redis-Cluster-{environment}',
            cluster_name=f'R2D2-Integration-Platform-Redis-{environment}',
            cache_node_type='cache.t3.micro',
            engine='redis',
            num_cache_nodes=1,
            cache_subnet_group_name=subnet_group.ref,
            vpc_security_group_ids=[redis_security_group.security_group_id],
                log_delivery_configurations=[
                    elasticache.CfnCacheCluster.LogDeliveryConfigurationRequestProperty(
                        destination_details=elasticache.CfnCacheCluster.DestinationDetailsProperty(
                            cloud_watch_logs_details=elasticache.CfnCacheCluster.CloudWatchLogsDestinationDetailsProperty(
                                log_group=f"R2D2-Integration-Platform-redis-logs-{environment}"
                            ),
                        ),
                        destination_type="cloudwatch-logs",
                        log_format="text",
                        log_type="engine-log"
                    )],
        )

        # Wait for the Redis cluster to be available before starting up the containers
        self.fargate_service.node.add_dependency(redis_cluster)

        # Output the Redis endpoint
        cdk.CfnOutput(self, 'Redis Endpoint URL and Port', value=f'{redis_cluster.attr_redis_endpoint_address}:{redis_cluster.attr_redis_endpoint_port}')

        # Set Redis URL and Port as environment variables
        self.fargate_container.add_environment('REDIS_HOST', redis_cluster.attr_redis_endpoint_address)
        self.fargate_container.add_environment('REDIS_PORT', redis_cluster.attr_redis_endpoint_port)

        # API Gateway and Cognito Authorizer
        self.cognito_pool_authorizer = self.create_cognito_pool_authorizer(cognito_user_pool_id,
                                                                           cognito_user_pool_client_ids)

        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.AnyPrincipal()],
            actions=["execute-api:Invoke"],
            resources=["arn:aws:execute-api:*:*/*/*/*", "*"]
        )

        self.vpc_link = apigatewayv2.VpcLink(self, f'R2D2-Integration-Platform-VPC-Link-{environment}',
                                             vpc_link_name=f'R2D2-Integration-Platform-VPC-Link-{environment}',
                                             vpc=self.vpc
                                             )

        self.api_gateway = apigatewayv2.HttpApi(self, f'R2D2-Integration-Platform-API-Gateway-GW-{environment}',
                                                api_name=f'R2D2-Integration-Platform-API-{environment}',
                                                description='This service serves R2D2-Integration-Platform APIs.',
                                                cors_preflight={
                                                    'allow_origins': ['*'],
                                                    'allow_methods': [apigatewayv2.CorsHttpMethod.ANY],
                                                    'allow_headers': ['*']
                                                }
                                                )

        api_gateway_default_stage = self.api_gateway.default_stage.node.default_child
        log_group = logs.LogGroup(self, f'R2D2-Integration-Platform-API-GW-AccessLogs-{environment}',
                                  retention=RetentionDays.THREE_MONTHS)

        api_gateway_default_stage.access_log_settings = {
            'destinationArn': log_group.log_group_arn,
            'format': json.dumps({
                'apiId': '$context.apiId',
                'requestId': '$context.requestId',
                'userAgent': '$context.identity.userAgent',
                'sourceIp': '$context.identity.sourceIp',
                'requestTime': '$context.requestTime',
                'httpMethod': '$context.httpMethod',
                'path': '$context.path',
                'status': '$context.status',
                'authorizerError': '$context.authorizer.error',
                'apiGatewayError': '$context.error.message'
            })
        }

        # Wait for the Fargate service to be available before starting up the API Gateway
        self.api_gateway.node.add_dependency(self.fargate_service)

        # Output the API Gateway endpoint
        cdk.CfnOutput(self, 'API Gateway Public Endpoint', value=self.api_gateway.url)

        # Management APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-Health-API',
                                   '/actuator/health',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        # Auth APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Oauth-Initiate-API',
                                   '/oauth/{crm_name}/initiate',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Oauth-Callback-API',
                                   '/oauth/{crm_name}/callback',
                                   apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Oauth-Revoke-API',
                                   '/oauth/{crm_name}/revoke',
                                   apigatewayv2.HttpMethod.PUT,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Oauth-Introspect-API',
                                   '/oauth/{crm_name}/introspect',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Oauth-Ping-API',
                                   '/oauth/{crm_name}/ping',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        # Hubspot APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Create-Contact-API',
                                   '/crm/hubspot/create-contact',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Bulk-Create-Contact-API',
                                   '/crm/hubspot/create-contact/bulk',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Bulk-Create-Contact-UI-API',
                                   '/crm/{crm_name}/bulk/{object_name}',
                                   apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Create-Email-API',
                                   '/crm/hubspot/create-email',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Get-Properties-API',
                                   '/crm/hubspot/{crm_object}/field-properties',
                                    apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Get-Contacts-By-Listid-API',
                                   '/crm/hubspot/contact',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Get-Contacts-By-Listid-API-Internal',
                                   '/crm/hubspot/contact/internal',
                                   apigatewayv2.HttpMethod.GET,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Get-All-Data-API',
                                    '/crm/hubspot/{crm_object}/all',
                                    apigatewayv2.HttpMethod.GET,
                                    None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Hubspot-Get-Contact-Lists-API',
                                    '/crm/hubspot/lists',
                                    apigatewayv2.HttpMethod.GET,
                                    self.cognito_pool_authorizer)

        # Salesforce APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Create-Contact-API',
                                   '/crm/salesforce/create-contact',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Bulk-Create-Contact-API',
                                   '/crm/salesforce/create-contact/bulk',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Create-Lead-API',
                                   '/crm/salesforce/leads',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Bulk-Create-Lead-API',
                                   '/crm/salesforce/leads/bulk',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Create-Email-API',
                                   '/crm/salesforce/create-email',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-All-Data-API',
                                   '/crm/salesforce/{crm_object}/all',
                                   apigatewayv2.HttpMethod.GET,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-Properties-API',
                                   '/crm/salesforce/{crm_object}/field-properties',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-Contacts-By-Listid-API',
                                   '/crm/salesforce/contact',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-Contacts-By-Listid-API-Internal',
                                   '/crm/salesforce/contact/internal',
                                   apigatewayv2.HttpMethod.GET,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-Contact-Lists-API',
                                   '/crm/salesforce/lists',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-CRM-Objects-API',
                                   '/crm/salesforce/crm-objects',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Query-API',
                                   '/crm/salesforce/query',
                                   apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Query-Internal-API',
                                   '/crm/salesforce/query/internal',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-Objects-API',
                                   '/crm/salesforce/objects',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Get-Object-Fields-API',
                                   '/crm/salesforce/fields',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Push-API',
                                   '/crm/salesforce/push',
                                   apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Push-Internal-API',
                                   '/crm/salesforce/push/internal',
                                   apigatewayv2.HttpMethod.POST,
                                   None)
        self.add_api_gateway_route('R2D2-Integration-Platform-Salesforce-Instance-Users-API',
                                   '/crm/salesforce/instance-users',
                                   apigatewayv2.HttpMethod.GET,
                                   None)

        # CRM v2 APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Create-Contact-API',
                                   '/v2/crm/{crm_name}/contacts',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Bulk-Create-Contacts-API',
                                   '/v2/crm/{crm_name}/contacts/bulk',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Create-Lead-API',
                                   '/v2/crm/{crm_name}/leads',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Bulk-Create-Leads-API',
                                   '/v2/crm/{crm_name}/leads/bulk',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Create-Object-API',
                                   '/v2/crm/{crm_name}/objects',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Bulk-Create-Objects-API',
                                   '/v2/crm/{crm_name}/objects/bulk',
                                   apigatewayv2.HttpMethod.POST,
                                   None) # authorizer enabled because Salesforce calls this from FE, changed on 2/25

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Create-Email-API',
                                   '/v2/crm/{crm_name}/emails',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Query-API',
                                   '/v2/crm/{crm_name}/query',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Check-API',
                                   '/v2/crm/{crm_name}/check',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Get-Lists-API',
                                   '/v2/crm/{crm_name}/lists',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)


        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Query-List-API',
                                   '/v2/crm/{crm_name}/lists',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Read-Objects-API',
                                   '/v2/crm/{crm_name}/objects',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Read-Push-Objects-API',
                                   '/v2/crm/{crm_name}/push-objects',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Read-Pull-Objects-API',
                                   '/v2/crm/{crm_name}/pull-objects',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Read-Fields-API',
                                   '/v2/crm/{crm_name}/fields',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Bulk-API',
                                   '/v2/crm/{crm_name}/bulk',
                                   apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Bulk-API',
                                   '/v2/crm/{crm_name}/agent/account',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-CRM-Bulk-API',
                                   '/v2/crm/{crm_name}/agent/contacts',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Enrich-From-CRM-API',
                                   '/v2/crm/{crm_name}/enrich-from-crm',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        # Configuration APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-Configuration-Get-Connected-CRM-API',
                                   '/crm/configuration',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Configuration-Initiate-API',
                                   '/crm/configuration/{crm_name}',
                                   apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Configuration-Update-API',
                                   '/crm/configuration/{crm_name}',
                                    apigatewayv2.HttpMethod.PUT,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Configuration-Get-API',
                                   '/crm/configuration/{crm_name}',
                                    apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Field-Mapping-Create-API',
                                   '/crm/configuration/{crm_name}/field-mapping',
                                    apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)


        self.add_api_gateway_route('R2D2-Integration-Platform-Field-Mapping-Get-API',
                                   '/crm/configuration/{crm_name}/field-mapping',
                                    apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Field-Mappings-Get-API',
                                   '/crm/configuration/{crm_name}/field-mappings',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Field-Mapping-Update-API',
                                   '/crm/configuration/{crm_name}/field-mapping',
                                    apigatewayv2.HttpMethod.PUT,
                                   self.cognito_pool_authorizer)
        
        self.add_api_gateway_route('R2D2-Integration-Platform-Field-Mappings-Delete-API',
                                   '/crm/configuration/{crm_name}/field-mapping',
                                   apigatewayv2.HttpMethod.DELETE,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Field-Salesforce-Contact-Check-API',
                                   '/crm/{crm_name}/contact/check',
                                    apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Transactions-Get-API',
                                   '/crm/transactions/{crm_name}',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Entity-Transactions-Get-API',
                                   '/crm/transactions/{crm_name}/{transaction_id}',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)
        
        self.add_api_gateway_route('R2D2-Integration-Platform-Configuration-Get-API',
                                   '/crm/configuration/{crm_name}/{user_id}',
                                    apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)
      
      
        #Calendar APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-Calendar-Get-API',
                                   '/calendar/configuration',
                                    apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Calendar-Update-API',
                                   '/calendar/configuration',
                                    apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Calendar-Get-List-API',
                                   '/calendar/scheduled',
                                    apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)
        

        self.add_api_gateway_route('R2D2-Integration-Platform-Calendar-Register-Configuration-API',
                                   '/integrations/register',
                                    apigatewayv2.HttpMethod.POST,
                                   None)
        
        self.add_api_gateway_route('R2D2-Integration-Platform-Calendar-Unregister-Configuration-API',
                                   '/integrations/unregister',
                                    apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Calendar-Get-Slots-API',
                                   '/calendar/integration/get-slots/{scheduling_id}',
                                    apigatewayv2.HttpMethod.GET,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Calendar-Create-Meeting-API',
                                   '/calendar/integration/book-meeting/{scheduling_id}',
                                    apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Recall-Integration-Webhook-API',
                                   '/recall/integration/webhook',
                                   apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Recall-Integration-Meetings-API',
                                   '/recall/integration/meetings',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Recall-Integration-Meeting-API',
                                   '/recall/integration/meeting',
                                   apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Recall-Integration-Webhook-API',
                                   '/recall/integration/unschedule/bot/{bot_id}',
                                   apigatewayv2.HttpMethod.DELETE,
                                   self.cognito_pool_authorizer)


        # BASEROW APIs
        self.add_api_gateway_route('R2D2-Integration-Platform-Baserow-Import-API',
                                   '/v2/crm/{crm_name}/baserow/import',
                                    apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Baserow-Export-API',
                                   '/v2/crm/{crm_name}/baserow/export',
                                    apigatewayv2.HttpMethod.POST,
                                   None)

        self.add_api_gateway_route('R2D2-Integration-Platform-Baserow-Import-Mapping-API',
                                   '/v2/crm/{crm_name}/baserow/mapping/{table_id}/{crm_object}/{research_job_id}',
                                    apigatewayv2.HttpMethod.GET,
                                   self.cognito_pool_authorizer)

        self.add_api_gateway_route('R2D2-Integration-Platform-Baserow-Export-Bulk-API',
                                   '/v2/crm/{crm_name}/baserow/export/bulk',
                                    apigatewayv2.HttpMethod.POST,
                                   self.cognito_pool_authorizer)

    def create_cognito_pool_authorizer(self, user_pool_id, user_pool_client_ids):
        user_pool = cognito.UserPool.from_user_pool_id(self, 'UserPool', user_pool_id)
        user_pool_clients = [cognito.UserPoolClient.from_user_pool_client_id(self,
                                                                             f'R2D2-Integration-Platform-UserPoolClient_{client_id}',
                                                                             client_id) for client_id in
                             user_pool_client_ids]
        return authorizers.HttpUserPoolAuthorizer('R2D2-Integration-Platform-CognitoAuthorizer', user_pool,
                                                  user_pool_clients=user_pool_clients,
                                                  identity_source=['$request.header.Authorization']
                                                  )

    def create_fargate_task_definition(self):
        task_definition_name = 'R2D2-Integration-Platform-ECS-Task-Definition'
        if platform.system() == "Darwin":
            return ecs.FargateTaskDefinition(
                    self, task_definition_name, memory_limit_mib=2048, cpu=512,
                    runtime_platform=ecs.RuntimePlatform(
                        operating_system_family=ecs.OperatingSystemFamily.LINUX,
                        cpu_architecture=ecs.CpuArchitecture.ARM64
                    )
                )
        return ecs.FargateTaskDefinition(self, task_definition_name,
                                         memory_limit_mib=2048,
                                         cpu=512
                                         )

    def create_fargate_container(self, environment):
        log_group = logs.LogGroup(self, "R2D2-Integration-Platform-Fargate-Container",
                                  log_group_name=f'R2D2-Integration-Platform-Logs-{environment}',
                                  retention=logs.RetentionDays.ONE_MONTH,
                                  removal_policy=RemovalPolicy.DESTROY
                                  )

        build_args = {
            'CODEARTIFACT_TOKEN': self.codeartifact_token
        }

        return self.fargate_task_definition.add_container('R2D2-Integration-Platform-Container',
                                                          image=ecs.ContainerImage.from_asset('./', build_args=build_args),
                                                          logging=ecs.LogDrivers.aws_logs(
                                                              stream_prefix='R2D2-Integration-Platform-Logs',
                                                              log_group=log_group
                                                          ),
                                                          memory_limit_mib=2048,
                                                          cpu=512,
                                                          port_mappings=[ecs.PortMapping(container_port=3002,
                                                                                         protocol=ecs.Protocol.TCP)]
                                                          )

    def add_api_gateway_route(self, id, path, method, authorizer):
        self.api_gateway.add_routes(
            path=path,
            methods=[method],
            integration=integrations.HttpAlbIntegration(
                id,
                self.fargate_service.listener,
                vpc_link=self.vpc_link,
                method=method
            ),
            authorizer=authorizer
        )
