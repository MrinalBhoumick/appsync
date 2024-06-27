#!/bin/bash

# Make sure API_ID, API_NAME, and AUTHENTICATION_TYPE are set before running this script

echo "Starting schema creation for AppSync API with API ID $API_ID"

# Fetch the GraphQL schema file from the repository
if curl -o schema.graphql "https://raw.githubusercontent.com/$GITHUB_REPOSITORY/$GITHUB_BRANCH/templates/data.graphql"; then
    echo "Schema file downloaded successfully."
else
    echo "Failed to download the schema file."
    exit 1
fi

# Encode the GraphQL schema file in base64
SCHEMA_BASE64=$(base64 -w 0 schema.graphql)

# Retry mechanism for updating the schema
retry_count=0
max_retries=5
retry_delay=10

update_schema() {
    aws appsync update-graphql-api --api-id "$API_ID" --name "$API_NAME" --authentication-type "$AUTHENTICATION_TYPE"
}

start_schema_creation() {
    aws appsync start-schema-creation --api-id "$API_ID" --definition "data:text/plain;base64,$SCHEMA_BASE64"
}

while [ $retry_count -lt $max_retries ]; do
    if update_schema; then
        echo "API name and authentication type updated successfully."
        break
    else
        echo "Failed to update API name and authentication type. Retrying in $retry_delay seconds..."
        sleep $retry_delay
        retry_count=$((retry_count + 1))
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "Max retries reached. Failed to update API name and authentication type."
    exit 1
fi

# Initiate schema creation for the AppSync API
if start_schema_creation; then
    echo "Schema update initiated successfully."
else
    echo "Failed to initiate schema update."
    exit 1
fi

echo "Schema update process completed."
