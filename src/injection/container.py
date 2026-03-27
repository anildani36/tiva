from dependency_injector import containers, providers
from jeeva.core.injection import BaseJeevaGateways, BaseJeevaServices, BaseJeevaApplication

from src.controllers.calendar.configuration_controller import CalendarConfigurationController
from src.controllers.calendar.integration_controller import CalendarIntegrationController
from src.controllers.integration_transaction_controller import IntegrationTransactionController
from src.controllers.pipedrive_auth_controller import PipedriveAuthController
from src.controllers.zoho_auth_controller import ZohoAuthController
from src.service.authentication.oauth_service import pipedrive_oauth_service, zoho_oauth_service
from src.service.calendar.configuration_service import CalendarConfigurationService
from src.service.database.calendar.calendar_user_name_count_db_service import CalendarUserNameCountDbService
from src.service.database.calendar.calendar_users_db_service import CalendarUsersDbService
from src.service.database.calendar.configuration_db_service import CalendarConfigurationDbService
from src.service.database.lead_generation_db_service import LeadGenerationDbService
from src.service.database.users_db_service import UsersDbService
from src.service.integration_transaction_service import IntegrationTransactionService
from src.controllers.salesforce_auth_controller import SalesforceAuthController
from src.controllers.salesforce_bulk_integration_queue_controller import SalesforceBulkIntegrationQueueController
from src.controllers.salesforce_controller import SalesforceController
from src.interceptors.salesforce_oauth_interceptor import SalesforceOauthInterceptor
from src.service.authentication.oauth_service.salesforce_oauth_service import SalesforceOauthService
from src.service.bulk_integration.salesforce_bulk_integration_queue_service import SalesforceBulkIntegrationQueueService
from src.service.database.enrichment_automation_leads_db_service import EnrichmentAutomationLeadsDbService
from src.service.database.unibox_user_db_service import UniboxUserDbService
from src.service.database.unibox_sent_db_service import UniboxSentDbService
from src.service.event_bridge_scheduler_service import EventBridgeSchedulerService
from src.controllers.hubspot_bulk_integration_queue_controller import HubspotBulkIntegrationQueueController
from src.service.bulk_integration.hubspot_bulk_integration_queue_service import HubspotBulkIntegrationQueueService
from src.service.database.integration_entity_transactions_db_service import IntegrationEntityTransactionsDbService
from src.service.database.integration_transaction_hashes_db_service import IntegrationTransactionHashesDbService
from src.service.database.r2d2_uploaded_lead_object_service import R2D2UploadedLeadObjectDbService
from src.service.database.r2d2_lead_object_db_service import R2D2LeadObjectDbService
from src.service.database.integration_transactions_db_service import IntegrationTransactionsDbService
from src.controllers.configuration_controller import ConfigurationController
from src.controllers.hubspot_controller import HubspotController
from src.service.configuration_service import UserConfigurationService
from src.service.database.integration_config_db_service import IntegrationConfigDbService
from src.service.database.integration_field_mapping_db_service import IntegrationFieldMappingDbService
from src.service.database.unibox_drafts_db_service import UniboxDraftsDbService
from src.service.integration.hubspot_integration_service import HubspotIntegrationService
from src.controllers.hubspot_auth_controller import HubspotAuthController
from src.interceptors.hubspot_oauth_interceptor import HubspotOauthInterceptor
from src.service.authentication.oauth_service.hubspot_oauth_service import HubspotOauthService
from src.service.database.integration_users_db_service import IntegrationUsersDbService
from src.service.integration.salesforce_integration_service import SalesforceIntegrationService
from src.service.integration_transaction_hashing_service import IntegrationTransactionHashingService
from src.service.messaging_queue_service import SQSMessagingQueueService
from src.service.redis_cache_service import RedisCacheService
from src.controllers.apideck_auth_controller import ApideckAuthController
from src.service.authentication.api_deck_authentication_service.api_deck_authentication_service import \
    ApiDeckAuthenticationService
from src.service.database.calendar.calender_scheduling_meeting_db_service import ScheduledMeetingDbService
from src.controllers.calendar.scheduled_meeting_controller import CalendarScheduledMeetingController
from src.service.calendar.integration.scheduled_meeting_service import ScheduledMeetingService

class Gateways(BaseJeevaGateways):
    ...


class Services(BaseJeevaServices):

    gateways = providers.DependenciesContainer()

    api_deck_authentication_service = providers.Factory(
        ApiDeckAuthenticationService
    )

    crm_authentication_controller = providers.Factory(
        ApideckAuthController,
        api_deck_authentication_service=api_deck_authentication_service
    )

    redis_cache_service = providers.Factory(RedisCacheService)

    sqs_messaging_queue_service = providers.Factory(
        SQSMessagingQueueService
    )

    integration_transaction_hashes_db_service = providers.Factory(
        IntegrationTransactionHashesDbService
    )

    integration_users_db_service = providers.Factory(
        IntegrationUsersDbService
    )

    integration_config_db_service = providers.Factory(
        IntegrationConfigDbService
    )

    integration_transaction_db_service = providers.Factory(
        IntegrationTransactionsDbService
    )

    integration_transaction_hashing_service = providers.Factory(
        IntegrationTransactionHashingService,
        integration_transaction_hashes_db_service=integration_transaction_hashes_db_service
    )

    integration_entity_transactions_db_service = providers.Factory(
        IntegrationEntityTransactionsDbService
    )

    r2d2_object_db_service = providers.Factory(
        R2D2LeadObjectDbService
    )

    r2d2_uploaded_lead_object_db_service = providers.Factory(
        R2D2UploadedLeadObjectDbService
    )

    integration_field_mapping_db_service = providers.Factory(
        IntegrationFieldMappingDbService
    )

    unibox_user_db_service = providers.Factory(
        UniboxUserDbService
    )

    unibox_drafts_db_service = providers.Factory(
        UniboxDraftsDbService
    )

    unibox_sent_db_service = providers.Factory(
        UniboxSentDbService
    )

    enrichment_automation_leads_db_service = providers.Factory(
        EnrichmentAutomationLeadsDbService
    )

    lead_generation_db_service = providers.Factory(
        LeadGenerationDbService
    )

    users_db_service = providers.Factory(
        UsersDbService
    )

    #Oauth services
    hubspot_oauth_service = providers.Factory(
        HubspotOauthService,
        redis_cache_service=redis_cache_service,
        integration_users_db_service=integration_users_db_service
    )
    salesforce_oauth_service = providers.Factory(
        SalesforceOauthService,
        redis_cache_service=redis_cache_service,
        integration_users_db_service=integration_users_db_service
    )
    zoho_oauth_service = providers.Factory(
        zoho_oauth_service.ZohoOauthService,
        redis_cache_service=redis_cache_service,
        integration_users_db_service=integration_users_db_service
    )

    pipedrive_oauth_service = providers.Factory(
        pipedrive_oauth_service.PipedriveOauthService,
        redis_cache_service=redis_cache_service,
        integration_users_db_service=integration_users_db_service
    )

    hubspot_oauth_controller = providers.Factory(
        HubspotAuthController,
        hubspot_oauth_service=hubspot_oauth_service
    )

    hubspot_oauth_interceptor = providers.Factory(
        HubspotOauthInterceptor,
        hubspot_oauth_service=hubspot_oauth_service,
        redis_cache_service=redis_cache_service
    )

    hubspot_integration_service = providers.Factory(
        HubspotIntegrationService,
        redis_cache_service=redis_cache_service,
        integration_transaction_db_service = integration_transaction_db_service,
        r2d2_object_db_service = r2d2_object_db_service,
        integration_field_mapping_db_service = integration_field_mapping_db_service,
        unibox_drafts_db_service=unibox_drafts_db_service,
        integration_transaction_hashing_service=integration_transaction_hashing_service,
        r2d2_uploaded_lead_object_db_service = r2d2_uploaded_lead_object_db_service,
        integration_entity_transactions_db_service=integration_entity_transactions_db_service
    )

    event_bridge_scheduler_service = providers.Factory(
        EventBridgeSchedulerService
    )

    user_configuration_service = providers.Factory(
        UserConfigurationService,
        integration_config_db_service=integration_config_db_service,
        integration_field_mapping_db_service=integration_field_mapping_db_service,
        event_bridge_scheduler_service=event_bridge_scheduler_service,
        integration_users_db_service=integration_users_db_service,
        salesforce_oauth_service=salesforce_oauth_service,
        hubspot_oauth_service=hubspot_oauth_service,
        zoho_oauth_service=zoho_oauth_service,
        pipedrive_oauth_service=pipedrive_oauth_service
    )

    salesforce_integration_service = providers.Factory(
        SalesforceIntegrationService,
        redis_cache_service=redis_cache_service,
        integration_transaction_db_service=integration_transaction_db_service,
        r2d2_object_db_service=r2d2_object_db_service,
        integration_field_mapping_db_service=integration_field_mapping_db_service,
        unibox_drafts_db_service=unibox_drafts_db_service,
        integration_transaction_hashing_service=integration_transaction_hashing_service,
        integration_users_db_service=integration_users_db_service,
        r2d2_uploaded_lead_object_db_service=r2d2_uploaded_lead_object_db_service,
        integration_entity_transactions_db_service=integration_entity_transactions_db_service,
        unibox_sent_db_service=unibox_sent_db_service,
        integration_config_db_service=integration_config_db_service,
        enrichment_automation_leads_db_service=enrichment_automation_leads_db_service,
        user_configuration_service= user_configuration_service,
        lead_generation_db_service=lead_generation_db_service
    )

    hubspot_controller = providers.Factory(
        HubspotController,
        hubspot_integration_service=hubspot_integration_service,
        integration_transaction_db_service=integration_transaction_db_service
    )

    integration_field_mapping_db_service = providers.Factory(
        IntegrationFieldMappingDbService
    )

    configuration_controller = providers.Factory(
        ConfigurationController,
        user_configuration_service=user_configuration_service
    )

    integration_transaction_service = providers.Factory(
        IntegrationTransactionService,
        integration_transaction_db_service=integration_transaction_db_service,
        integration_entity_transactions_db_service=integration_entity_transactions_db_service,
        integration_users_db_service=integration_users_db_service
    )

    integration_transaction_controller = providers.Factory(
        IntegrationTransactionController,
        integration_transaction_service=integration_transaction_service
    )

    hubspot_bulk_integration_queue_service = providers.Factory(
        HubspotBulkIntegrationQueueService,
        sqs_messaging_queue_service=sqs_messaging_queue_service,
        integration_transaction_db_service=integration_transaction_db_service
    )

    hubspot_bulk_integration_queue_controller = providers.Factory(
        HubspotBulkIntegrationQueueController,
        hubspot_bulk_integration_queue_service=hubspot_bulk_integration_queue_service
    )

    salesforce_bulk_integration_queue_service = providers.Factory(
        SalesforceBulkIntegrationQueueService,
        sqs_messaging_queue_service=sqs_messaging_queue_service,
        integration_transaction_db_service=integration_transaction_db_service
    )

    salesforce_bulk_integration_queue_controller = providers.Factory(
        SalesforceBulkIntegrationQueueController,
        salesforce_bulk_integration_queue_service=salesforce_bulk_integration_queue_service
    )


    salesforce_oauth_controller = providers.Factory(
        SalesforceAuthController,
        salesforce_oauth_service=salesforce_oauth_service
    )

    salesforce_oauth_interceptor = providers.Factory(
        SalesforceOauthInterceptor,
        salesforce_oauth_service=salesforce_oauth_service,
        redis_cache_service=redis_cache_service
    )

    salesforce_controller = providers.Factory(
        SalesforceController,
        salesforce_integration_service=salesforce_integration_service,
        integration_transaction_db_service=integration_transaction_db_service,
        salesforce_oauth_service=salesforce_oauth_service,
        redis_cache_service=redis_cache_service,
        integration_users_db_service=integration_users_db_service
    )


    zoho_oauth_controller = providers.Factory(
        ZohoAuthController,
        zoho_oauth_service=zoho_oauth_service
    )

    pipedrive_oauth_controller = providers.Factory(
        PipedriveAuthController,
        pipedrive_oauth_service=pipedrive_oauth_service
    )


    # Calendar Services
    calendar_configuration_db_service = providers.Factory(
        CalendarConfigurationDbService
    )

    calendar_users_db_service = providers.Factory(
        CalendarUsersDbService
    )

    calendar_user_name_count_db_service = providers.Factory(
        CalendarUserNameCountDbService
    )

    calendar_configuration_service = providers.Factory(
        CalendarConfigurationService,
        calendar_configuration_db_service=calendar_configuration_db_service,
        calendar_user_name_count_db_service=calendar_user_name_count_db_service,
        users_db_service=users_db_service,
        unibox_user_db_service=unibox_user_db_service
    )

    calendar_configuration_controller = providers.Factory(
        CalendarConfigurationController,
        calendar_configuration_service=calendar_configuration_service
    )

    calendar_integration_controller = providers.Factory(
        CalendarIntegrationController
    )

    calendar_db_service = providers.Factory(
        CalendarUsersDbService
    )

    scheduled_meeting_db_service = providers.Factory(
        ScheduledMeetingDbService
    )

    scheduled_meeting_service = providers.Factory(
        ScheduledMeetingService,
        scheduled_meeting_db_service=scheduled_meeting_db_service
    )

    calendar_scheduled_meeting_controller = providers.Factory(
        CalendarScheduledMeetingController,
        scheduled_meeting_service=scheduled_meeting_service
    )

class Application(BaseJeevaApplication):

    wiring_config = containers.WiringConfiguration(modules=[
        'src.routes.api_routes',
        'src.routes.hubspot_oauth_routes',
        'src.routes.apideck_auth_routes',
        'src.routes.hubspot_routes',
        'src.routes.configuration_routes',
        'src.routes.hubspot_bulk_integration_queue_routes',
        'src.routes.salesforce_oauth_routes',
        'src.routes.salesforce_routes',
        'src.routes.salesforce_routes_internal',
        'src.routes.salesforce_bulk_integration_queue_routes',
        'src.routes.transaction_routes',

        'src.routes.zoho_oauth_routes',
        'src.routes.pipedrive_oauth_routes',
        
        'src.routes.calendar.configuration_routes',
        'src.routes.calendar.integration_routes',
        'src.routes.calendar.scheduled_meeting_router',
        'src.routes.integrations_routes',
    ])

    gateways = providers.Container(
        Gateways
    )

    services = providers.Container(
        Services,
        gateways=gateways,
    )


container = Application()
container.wire(modules=[__name__])