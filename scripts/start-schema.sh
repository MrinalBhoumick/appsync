#!/bin/bash

# Make sure API_ID is set before running this script
# Set the path to the schema file
SCHEMA_FILE="templates/data.graphql"

echo "Starting schema creation for AppSync API with API ID $API_ID"

# Update the schema for the AppSync API
if aws appsync update-graphql-schema --api-id "$API_ID" --definition "file://$SCHEMA_FILE"; then
    echo "Schema updated successfully."
else
    echo "Failed to update schema."
    exit 1
fi

echo "Schema update process completed."
