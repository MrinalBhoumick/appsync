#!/bin/bash

# Make sure API_ID is set before running this script
# Set the path to the schema file
SCHEMA_FILE="templates/data.graphql"

echo "Starting schema creation for AppSync API with API ID $API_ID"

# Encode the GraphQL schema file in base64
SCHEMA_BASE64=$(base64 -w 0 "$SCHEMA_FILE")

# Initiate schema creation for the AppSync API
if aws appsync start-schema-creation --api-id "$API_ID" --definition "data:text/plain;base64,$SCHEMA_BASE64"; then
    echo "Schema creation initiated successfully."
else
    echo "Failed to initiate schema creation."
    exit 1
fi

# Optional: adjust sleep time as needed to ensure the schema creation process has time to start
sleep 10

echo "Schema creation process completed."
