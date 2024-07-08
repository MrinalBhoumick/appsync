import boto3
import os
import requests
from requests_aws4auth import AWS4Auth

# Initialize environment variables
API_ID = os.getenv('API_ID')
GITHUB_REPO_URL = os.getenv('GITHUB_REPO_URL')
API_NAME = os.getenv('API_NAME')
AUTHENTICATION_TYPE = os.getenv('AUTHENTICATION_TYPE')
LAMBDA_FUNCTION_ARN = os.getenv('LAMBDA_FUNCTION_ARN')
REGION = os.getenv('REGION')
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

# Load the request and response mapping templates for queries
with open(query_mapping_path, 'r') as query_mapping_file:
    query_mapping_template = query_mapping_file.read()

# Load the request and response mapping templates for mutations
with open(mutation_mapping_path, 'r') as mutation_mapping_file:
    mutation_mapping_template = mutation_mapping_file.read()

# Load the request mapping template
with open(request_mapping_path, 'r') as request_mapping_file:
    request_mapping_template = request_mapping_file.read()

# Start the schema creation
response = client.start_schema_creation(
    apiId=API_ID,
    definition=schema_content.encode('utf-8')
)

print(response)

# Introspection query to fetch all types and fields
introspection_query = {
    'query': '''
    {
        __schema {
            types {
                name
                fields {
                    name
                }
            }
        }
    }
    '''
}

# Use boto3 to get AWS credentials
session = boto3.Session()
credentials = session.get_credentials().get_frozen_credentials()

auth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'appsync', session_token=credentials.token)

headers = {
    'Content-Type': 'application/json'
}

# Make the request to the API
print(f"Making request to {API_URL} with query: {introspection_query}")
response = requests.post(API_URL, json=introspection_query, headers=headers, auth=auth)

# Check for HTTP errors
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
    print(f"Response content: {response.content}")
    raise

# Parse the response as JSON
schema_data = response.json()

# Debugging: Print the entire response content
print(schema_data)

# Extract the fields from the introspection query result
fields = []
if 'data' in schema_data and '__schema' in schema_data['data']:
    for type_data in schema_data['data']['__schema']['types']:
        if 'fields' in type_data:
            for field in type_data['fields']:
                fields.append((type_data['name'], field['name']))

print(fields)  # This will print all type and field name pairs

def get_service_role():
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

# Fetch the service role dynamically
service_role_arn = get_service_role()

# Update resolvers for all fields
for type_name, field_name in fields:
    if type_name in ['Query', 'Mutation']:
        if type_name == 'Query':
            update_resolver(
                api_id=API_ID,
                type_name=type_name,
                field_name=field_name,
                request_mapping_template=query_mapping_template,
                response_mapping_template=query_mapping_template,
                service_role_arn=service_role_arn
            )
        elif type_name == 'Mutation':
            update_resolver(
                api_id=API_ID,
                type_name=type_name,
                field_name=field_name,
                request_mapping_template=mutation_mapping_template,
                response_mapping_template=mutation_mapping_template,
                service_role_arn=service_role_arn
            )
