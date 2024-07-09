import boto3
import os

# Initialize environment variables
API_ID = os.getenv('API_ID')
REGION = os.getenv('REGION')
SERVICE_ROLE_ARN = os.getenv('SERVICE_ROLE_ARN')

# Initialize the AppSync client
client = boto3.client('appsync', region_name=REGION)

# Define the paths for response mapping templates
query_mapping_path = os.path.join('templates', 'response_mapping_query.graphql')
mutation_mapping_path = os.path.join('templates', 'response_mapping_mutation.graphql')

# Load the response mapping templates
with open(query_mapping_path, 'r') as query_mapping_file:
    query_mapping_template = query_mapping_file.read()

with open(mutation_mapping_path, 'r') as mutation_mapping_file:
    mutation_mapping_template = mutation_mapping_file.read()

# Function to update resolver in AWS AppSync
def update_resolver(api_id, type_name, field_name, response_mapping_template, service_role_arn):
    data_source_name = f'{type_name}_{field_name}_DataSource'

    try:
        response = client.update_resolver(
            apiId=api_id,
            typeName=type_name,
            fieldName=field_name,
            dataSourceName=data_source_name,
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
            responseMappingTemplate=response_mapping_template
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
    if type_name == 'Query':
        update_resolver(
            api_id=API_ID,
            type_name=type_name,
            field_name=field_name,
            response_mapping_template=query_mapping_template,
            service_role_arn=SERVICE_ROLE_ARN
        )
    elif type_name == 'Mutation':
        update_resolver(
            api_id=API_ID,
            type_name=type_name,
            field_name=field_name,
            response_mapping_template=mutation_mapping_template,
            service_role_arn=SERVICE_ROLE_ARN
        )
