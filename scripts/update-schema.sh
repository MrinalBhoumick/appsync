#!/bin/bash

# Configure AWS CLI if not already configured
if [[ ! -f ~/.aws/credentials ]]; then
    echo "AWS CLI is not configured. Configuring AWS CLI..."
    aws configure
fi

# Fetch AppSync API ID from CodeBuild environment
if [[ -z "$API_ID" ]]; then
    echo "Error: API_ID environment variable is not set."
    exit 1
fi

API_ID="$API_ID"

# Determine the path to the templates directory relative to the script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TEMPLATES_DIR="$SCRIPT_DIR/../templates"
SCHEMA_FILE="$TEMPLATES_DIR/data.graphql"

# Check if the schema file exists and is not empty
if [[ ! -s $SCHEMA_FILE ]]; then
    echo "Error: Schema file not found or is empty: $SCHEMA_FILE"
    exit 1
fi

# Update the AppSync API schema using appsync-schema-uploader
echo "Updating AppSync API schema..."
python3 -m appsync_schema_uploader --api-id "$API_ID" --schema "$SCHEMA_FILE"

echo "Schema update process completed."
