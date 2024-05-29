#!/bin/bash

# Make sure API_ID, API_NAME, and AUTHENTICATION_TYPE are set before running this script


echo "Starting schema creation for AppSync API with API ID $API_ID"

# Fetch the GraphQL schema file from GitHub
if curl -o schema.graphql "$GITHUB_REPO_URL/templates/data.graphql"; then
    echo "Schema file downloaded successfully."
else
    echo "Failed to download the schema file."
    exit 1
fi

# Encode the GraphQL schema file in base64
SCHEMA_BASE64=$(base64 -w 0 schema.graphql)

# Initiate schema creation for the AppSync API
if aws appsync update-graphql-api --api-id "$API_ID" --name "$API_NAME" --authentication-type "$AUTHENTICATION_TYPE" --definition "data:text/plain;base64,$SCHEMA_BASE64"; then
    echo "Schema update initiated successfully."
else
    echo "Failed to initiate schema update."
    exit 1
fi

echo "Schema update process completed."
