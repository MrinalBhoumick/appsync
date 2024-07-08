import boto3
import os

# Initialize environment variables
API_ID = os.getenv('API_ID')
REGION = os.getenv('REGION')

# Initialize the AppSync client
client = boto3.client('appsync', region_name=REGION)

# Define the path for the GraphQL schema
schema_path = os.path.join('templates', 'data.graphql')

# Load the GraphQL schema
with open(schema_path, 'r') as schema_file:
    schema_content = schema_file.read()

# Start the schema creation or update
response = client.start_schema_creation(
    apiId=API_ID,
    definition=schema_content.encode('utf-8')
)

# Check if the schema update was successful
if response['ResponseMetadata']['HTTPStatusCode'] == 200:
    print("Schema Updated successfully")
else:
    print("Schema Update failed")

