import boto3
import os
import requests
import time
from requests_aws4auth import AWS4Auth

# Initialize environment variables
API_ID = os.getenv('API_ID')
REGION = os.getenv('REGION')
LAMBDA_FUNCTION_ARN = os.getenv('LAMBDA_FUNCTION_ARN')
API_URL = os.getenv('API_URL')

# Initialize the AppSync client
client = boto3.client('appsync', region_name=REGION)

# Define the paths for schema and mapping templates
schema_path = os.path.join('templates', 'data.graphql')
query_mapping_path = os.path.join('templates', 'response_mapping_query.graphql')
mutation_mapping_path = os.path.join('templates', 'response_mapping_mutation.graphql')
request_mapping_path = os.path.join('templates', 'request_mapping.graphql')

# Load the GraphQL schema
with open(schema_path, 'r') as schema_file:
    schema_content = schema_file.read()

# Function to start schema creation
def start_schema_creation(api_id, schema_content):
    try:
        response = client.start_schema_creation(
            apiId=api_id,
            definition=schema_content.encode('utf-8')
        )
        return response['status']
    except Exception as e:
        print(f"Failed to start schema creation: {e}")
        return None

# Wait for schema creation to complete
def wait_for_schema_creation(api_id):
    while True:
        try:
            response = client.get_schema_creation_status(
                apiId=api_id
            )
            status = response['status']
            if status == 'SUCCESS':
                print("Schema creation completed successfully")
                break
            elif status == 'FAILED':
                print("Schema creation failed")
                exit(1)
            print("Schema creation in progress. Waiting...")
            time.sleep(10)  # Wait for 10 seconds before retrying
        except Exception as e:
            print(f"Failed to get schema creation status: {e}")
            exit(1)

# Start schema creation
try:
    status = start_schema_creation(API_ID, schema_content)
    if status == 'PROCESSING':
        wait_for_schema_creation(API_ID)
    else:
        print("Failed to start schema creation or schema creation status not PROCESSING")
        exit(1)
except Exception as e:
    print(f"Failed to start schema creation: {e}")
    exit(1)

# Function to fetch current resolvers from AWS AppSync
def fetch_current_resolvers(api_id):
    resolvers = []
    paginator = client.get_paginator('list_resolvers')
    try:
        for page in paginator.paginate(apiId=api_id):
            for resolver in page['resolvers']:
                resolvers.append(resolver)
        return resolvers
    except Exception as e:
        print(f"Failed to fetch resolvers: {e}")
        return None

def get_service_role():
    try:
        # Create an IAM client
        iam_client = boto3.client('iam')

        # List roles with a specific path or tag (customize this as needed)
        roles = iam_client.list_roles(PathPrefix='/service-role/')

        # Find the role that matches your criteria (customize this as needed)
        for role in roles['Roles']:
            if 'service-role' in role['RoleName']:
                return role['Arn']

        # If no role matches, raise an exception or handle accordingly
        raise Exception("Service role not found")
    
    except Exception as e:
        print(f"Error fetching service role: {e}")
        exit(1)

# Function to compare local schema with current resolvers
def compare_schemas(local_schema, current_resolvers):
    # Parse local schema to extract resolvers
    local_resolvers = parse_resolvers(local_schema)

    # Compare with current resolvers in AppSync
    if not local_resolvers or not current_resolvers:
        return False

    # Check if resolvers match
    local_resolver_names = set((resolver['fieldName'], resolver['typeName']) for resolver in local_resolvers)
    current_resolver_names = set((resolver['fieldName'], resolver['typeName']) for resolver in current_resolvers)

    return local_resolver_names == current_resolver_names

# Function to parse resolvers from schema content
def parse_resolvers(schema_content):
    resolvers = []
    lines = schema_content.splitlines()
    current_type = None
    for line in lines:
        line = line.strip()
        if line.startswith("type "):
            current_type = line.split()[1]
        elif line.startswith("  "):
            if "(" in line:
                field_name = line.split("(")[0].strip()
                resolvers.append({'fieldName': field_name, 'typeName': current_type})
    return resolvers

# Function to update resolver in AWS AppSync
def update_resolver(api_id, type_name, field_name, request_mapping_template, response_mapping_template, service_role_arn):
    data_source_name = f'{type_name}_{field_name}_DataSource'

    create_or_update_data_source(api_id, data_source_name, LAMBDA_FUNCTION_ARN, service_role_arn)

    try:
        response = client.update_resolver(
            apiId=api_id,
            typeName=type_name,
            fieldName=field_name,
            dataSourceName=data_source_name,
            requestMappingTemplate=request_mapping_template,
            responseMappingTemplate=response_mapping_template
        )
        print(f'Successfully updated resolver for {type_name}.{field_name}')
    except client.exceptions.ResolverNotFoundException:
        print(f'Resolver for {type_name}.{field_name} not found. Creating a new one.')
        response = client.create_resolver(
            apiId=api_id,
            typeName=type_name,
            fieldName=field_name,
            dataSourceName=data_source_name,
            requestMappingTemplate=request_mapping_template,
            responseMappingTemplate=response_mapping_template
        )
        print(f'Successfully created resolver for {type_name}.{field_name}')

# Function to create or update data source in AWS AppSync
def create_or_update_data_source(api_id, data_source_name, lambda_arn, service_role_arn):
    try:
        # Check if data source exists
        response = client.get_data_source(
            apiId=api_id,
            name=data_source_name
        )
        # Update the existing data source
        response = client.update_data_source(
            apiId=api_id,
            name=data_source_name,
            type='AWS_LAMBDA',
            lambdaConfig={
                'lambdaFunctionArn': lambda_arn
            },
            serviceRoleArn=service_role_arn
        )
        print(f'Updated data source {data_source_name}')
    except client.exceptions.NotFoundException:
        # Create a new data source
        response = client.create_data_source(
            apiId=api_id,
            name=data_source_name,
            type='AWS_LAMBDA',
            lambdaConfig={
                'lambdaFunctionArn': lambda_arn
            },
            serviceRoleArn=service_role_arn
        )
        print(f'Created data source {data_source_name}')

# Fetch the service role dynamically
service_role_arn = get_service_role()

# Load the mapping templates
with open(request_mapping_path, 'r') as request_mapping_file:
    request_mapping_template = request_mapping_file.read()

with open(query_mapping_path, 'r') as query_mapping_file:
    query_mapping_template = query_mapping_file.read()

with open(mutation_mapping_path, 'r') as mutation_mapping_file:
    mutation_mapping_template = mutation_mapping_file.read()

# Fetch current resolvers from AWS AppSync
current_resolvers = fetch_current_resolvers(API_ID)

if current_resolvers is None:
    print("Failed to fetch current resolvers. Exiting.")
    exit(1)

# Compare local schema with current resolvers
if compare_schemas(schema_content, current_resolvers):
    print("No changes detected in resolvers. Skipping update.")
else:
    # Update resolvers for all fields
    for resolver in parse_resolvers(schema_content):
        type_name = resolver['typeName']
        field_name = resolver['fieldName']
        if type_name in ['Query', 'Mutation']:
            if type_name == 'Query':
                update_resolver(
                    api_id=API_ID,
                    type_name=type_name,
                    field_name=field_name,
                    request_mapping_template=request_mapping_template,
                    response_mapping_template=query_mapping_template,
                    service_role_arn=service_role_arn
                )
            elif type_name == 'Mutation':
                update_resolver(
                    api_id=API_ID,
                    type_name=type_name,
                    field_name=field_name,
                    request_mapping_template=request_mapping_template,
                    response_mapping_template=mutation_mapping_template,
                    service_role_arn=service_role_arn
                )

