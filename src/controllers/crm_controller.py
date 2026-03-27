import logging

from src.api.crm_base_api_service import CRMBaseAPIService
from src.decorators.custom_logging import async_custom_logging
from src.service.database.baserow_crm.baserow_service import BaseRowService
from src.schema.baserow_transformation.baserow_crm_transformation_db_schema import BaserowCRMTransformation

logger = logging.getLogger(__name__)

# Contacts
@async_custom_logging
async def create_contact_controller(base_api: CRMBaseAPIService):
    return await base_api.create_contact_service()

@async_custom_logging
async def create_contacts_controller(base_api: CRMBaseAPIService):
    return await base_api.create_contacts_service()

# Leads
@async_custom_logging
async def create_lead_controller(base_api: CRMBaseAPIService):
    return await base_api.create_lead_service()

@async_custom_logging
async def create_leads_controller(base_api: CRMBaseAPIService):
    return await base_api.create_leads_service()

# Custom Objects
@async_custom_logging
async def create_object_controller(base_api: CRMBaseAPIService):
    return await base_api.create_object_service()

@async_custom_logging
async def create_objects_controller(base_api: CRMBaseAPIService):
    return await base_api.create_objects_service()

# Email
@async_custom_logging
async def create_email_controller(base_api: CRMBaseAPIService):
    return await base_api.create_email_service()

# Query
@async_custom_logging
async def query_object_controller(base_api: CRMBaseAPIService):
    return await base_api.query_object_service()

# Check
@async_custom_logging
async def check_object_controller(base_api: CRMBaseAPIService):
    return await base_api.check_object_service()

# Lists
@async_custom_logging
async def get_all_lists_controller(base_api: CRMBaseAPIService):
    return await base_api.get_all_lists_service()

@async_custom_logging
async def query_lists_for_contacts_controller(base_api: CRMBaseAPIService):
    return await base_api.query_list_for_contacts_service()

# Get all objects
@async_custom_logging
async def get_all_objects_from_crm_controller(base_api: CRMBaseAPIService):
    return await base_api.get_all_objects_from_crm_service()

@async_custom_logging
async def get_all_push_enabled_enrichment_compatible_objects_controller(base_api: CRMBaseAPIService):
    base_api.integration_request_dto.objectTransactionType = 'push'
    return await base_api.get_all_enrichment_compatible_objects_service()

@async_custom_logging
async def get_all_pull_enabled_enrichment_compatible_objects_controller(base_api: CRMBaseAPIService):
    base_api.integration_request_dto.objectTransactionType = 'pull'
    return await base_api.get_all_enrichment_compatible_objects_service()

# Fields
@async_custom_logging
async def get_all_fields_for_object_controller(base_api: CRMBaseAPIService):
    return await base_api.get_all_fields_for_object_from_crm_service()

@async_custom_logging
async def initiate_bulk_integration_controller(base_api: CRMBaseAPIService):
    return await base_api.initiate_bulk_integration_service()

@async_custom_logging
async def agent_find_account_controller(base_api: CRMBaseAPIService):
    return await base_api.agent_find_account_service()

@async_custom_logging
async def agent_find_contacts_controller(base_api: CRMBaseAPIService):
    return await base_api.agent_find_contacts_service()

@async_custom_logging
async def enrich_from_crm_controller(base_api: CRMBaseAPIService):
    return await base_api.enrich_from_crm_service()

# CRM-Baserow Data Sync
@async_custom_logging
async def baserow_pull_data_controller(base_api: CRMBaseAPIService, baserow_service: BaseRowService):
    return await base_api.pull_from_crm_to_baserow_table_service(baserow_service=baserow_service)

@async_custom_logging
async def baserow_push_data_controller(base_api: CRMBaseAPIService):
    return await base_api.push_to_crm_from_baserow_table_service()

@async_custom_logging
async def get_baserow_mapping_controller(base_api: CRMBaseAPIService, table_id: int, crm_object: str, research_job_id: str):
    return await base_api.get_baserow_mapping_service(table_id=table_id, crm_object=crm_object, research_job_id=research_job_id)

@async_custom_logging
async def baserow_push_data_bulk_controller(base_api: CRMBaseAPIService, user_auth_token: str):
    return await base_api.baserow_push_data_bulk_service(user_auth_token=user_auth_token)