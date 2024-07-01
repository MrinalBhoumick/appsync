#!/bin/bash

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi


# Configure AWS CLI if not already configured
if [[ ! -f ~/.aws/credentials ]]; then
    echo "AWS CLI is not configured. Configuring AWS CLI..."
    aws configure
fi

# Fetch AppSync API ID from CodeBuild environment
if [[ -z "$API_ID" ]]; then
    echo "Error: AWS_APPSYNC_API_ID environment variable is not set."
    exit 1
fi

API_ID="$API_ID"

# Determine the path to the templates directory relative to the script's location
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
TEMPLATES_DIR="$SCRIPT_DIR/../templates"
SCHEMA_FILE="$TEMPLATES_DIR/data.graphql"

# Check if the schema file exists and is not empty
if [[ ! -s $SCHEMA_FILE ]]; then
    echo "Error: Schema file not found or is empty: $SCHEMA_FILE"
    exit 1
fi

# Base64 encode the schema file
SCHEMA_BASE64=$(base64 -w 0 "$SCHEMA_FILE")

# Initiate schema update for the AppSync API using AWS CLI
echo "Updating AppSync API schema..."
aws appsync start-schema-creation \
    --api-id "$API_ID" \
    --definition "data:text/plain;base64,$SCHEMA_BASE64"

# Optional: adjust sleep time as needed to ensure the schema creation process has time to start
sleep 10

echo "Schema update process completed."
