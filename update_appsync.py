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

# Define the introspection query
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
try:
    response = requests.post(API_URL, json=introspection_query, headers=headers, auth=auth)
    response.raise_for_status()
    schema_data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error during introspection query: {e}")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    exit(1)
except Exception as e:
    print(f"Unhandled exception: {e}")
    exit(1)

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

# Load the mapping templates
with open(request_mapping_path, 'r') as request_mapping_file:
    request_mapping_template = request_mapping_file.read()

with open(query_mapping_path, 'r') as query_mapping_file:
    query_mapping_template = query_mapping_file.read()

with open(mutation_mapping_path, 'r') as mutation_mapping_file:
    mutation_mapping_template = mutation_mapping_file.read()

# Update resolvers for all fields
for type_name, field_name in fields:
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
