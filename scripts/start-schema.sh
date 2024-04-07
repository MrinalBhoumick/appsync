#!/bin/bash

# Make sure GITHUB_REPO_URL, API_ID, API_NAME, and AUTHENTICATION_TYPE are set before running this script

echo "Starting schema creation for AppSync API from $GITHUB_REPO_URL"

# Fetch the GraphQL schema file from GitHub
if curl -o schema.graphql "$GITHUB_REPO_URL"; then
    echo "Schema file downloaded successfully."
else
    echo "Failed to download the schema file."
    exit 1
fi

# Encode the GraphQL schema file in base64
SCHEMA_BASE64=$(base64 -w 0 schema.graphql)

# Initiate schema creation for the AppSync API
if aws appsync start-schema-creation --api-id "$API_ID" --definition "data:text/plain;base64,$SCHEMA_BASE64"; then
    echo "Schema creation initiated successfully."
else
    echo "Failed to initiate schema creation."
    exit 1
fi

# Optional: adjust sleep time as needed to ensure the schema creation process has time to start
sleep 10

# Update the AppSync API with a new name and authentication type
if aws appsync update-graphql-api --api-id "$API_ID" --name "$API_NAME" --authentication-type "$AUTHENTICATION_TYPE"; then
    echo "AppSync API updated successfully."
else
    echo "Failed to update the AppSync API."
    exit 1
fi

echo "Schema update process completed."
