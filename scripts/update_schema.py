import boto3
import os
import time

# Initialize environment variables
API_ID = os.getenv('API_ID')
REGION = os.getenv('REGION')

# Initialize the AppSync client
client = boto3.client('appsync', region_name=REGION)

# Define the path for schema
schema_path = os.path.join('templates', 'data.graphql')

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
                print(f"Schema creation failed: {response['details']}")
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
