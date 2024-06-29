import boto3
import os

# AWS AppSync API ID
API_ID = "6o2znoypyjdthf6vdtf6rhwnz4"

# Path to your local GraphQL schema file
LOCAL_SCHEMA_FILE = "C:/Users/Mrinal Bhoumick/OneDrive - Workmates Core2Cloud Solution Pvt Ltd/Desktop/AppSync/templates/data.graphql"

def update_schema(api_id, schema_file):
    # Read local schema file content
    with open(schema_file, 'r') as f:
        schema_definition = f.read()

    try:
        # Initialize AppSync client
        client = boto3.client('appsync')

        # Update schema in AWS AppSync
        response = client.start_schema_creation(
            apiId=api_id,
            definition=schema_definition
        )

        print("Schema update started successfully")
    except Exception as e:
        print(f"Error updating schema: {e}")

def main():
    # Check if the local schema file exists
    if not os.path.isfile(LOCAL_SCHEMA_FILE):
        print(f"Schema file does not exist: {LOCAL_SCHEMA_FILE}")
        return
    
    # Update schema in AWS AppSync
    print("Updating schema in AWS AppSync...")
    update_schema(API_ID, LOCAL_SCHEMA_FILE)

if __name__ == "__main__":
    main()
