import boto3
import os

print("Updating request template")

# Initialize environment variables
API_ID = os.getenv('API_ID')
REGION = os.getenv('REGION')
LAMBDA_FUNCTION_ARN = os.getenv('LAMBDA_FUNCTION_ARN')
SERVICE_ROLE_ARN = os.getenv('SERVICE_ROLE_ARN')

# Initialize the AppSync client
client = boto3.client('appsync', region_name=REGION)

# Define the request mapping template path
request_mapping_path = os.path.join('templates', 'request_mapping.graphql')

# Load the request mapping template
with open(request_mapping_path, 'r') as request_mapping_file:
    request_mapping_template = request_mapping_file.read()

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

# Function to update resolver in AWS AppSync
def update_resolver(api_id, type_name, field_name, request_mapping_template, service_role_arn):
    data_source_name = f'{type_name}_{field_name}_DataSource'

    create_or_update_data_source(api_id, data_source_name, LAMBDA_FUNCTION_ARN, service_role_arn)

    try:
        response = client.update_resolver(
            apiId=api_id,
            typeName=type_name,
            fieldName=field_name,
            dataSourceName=data_source_name,
            requestMappingTemplate=request_mapping_template
        )
        print(f'Successfully updated resolver for {type_name}.{field_name}')
    except client.exceptions.ResolverNotFoundException:
        print(f'Resolver for {type_name}.{field_name} not found. Creating a new one.')
        response = client.create_resolver(
            apiId=api_id,
            typeName=type_name,
            fieldName=field_name,
            dataSourceName=data_source_name,
            requestMappingTemplate=request_mapping_template
        )
        print(f'Successfully created resolver for {type_name}.{field_name}')

# Function to fetch current resolvers from AWS AppSync
def fetch_current_resolvers(api_id):
    resolvers = []
    paginator = client.get_paginator('list_resolvers')
    
    try:
        # Iterate through each type (Query, Mutation, etc.)
        for type_name in ['Query', 'Mutation']:
            # Paginate through resolvers for each type
            for page in paginator.paginate(apiId=api_id, typeName=type_name):
                for resolver in page['resolvers']:
                    resolvers.append(resolver)
                    
        return resolvers
    
    except Exception as e:
        print(f"Failed to fetch resolvers: {e}")
        return None

# Load the GraphQL schema
schema_path = os.path.join('templates', 'data.graphql')
with open(schema_path, 'r') as schema_file:
    schema_content = schema_file.read()

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

# Fetch current resolvers from AWS AppSync
current_resolvers = fetch_current_resolvers(API_ID)

if current_resolvers is None:
    print("Failed to fetch current resolvers. Exiting.")
    exit(1)

# Update resolvers for all fields
for resolver in parse_resolvers(schema_content):
    type_name = resolver['typeName']
    field_name = resolver['fieldName']
    if type_name in ['Query', 'Mutation']:
        update_resolver(
            api_id=API_ID,
            type_name=type_name,
            field_name=field_name,
            request_mapping_template=request_mapping_template,
            service_role_arn=SERVICE_ROLE_ARN
        )
