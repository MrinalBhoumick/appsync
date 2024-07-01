#!/bin/bash

# Check if AWS CLI and Python are installed
command -v aws >/dev/null 2>&1 || { echo >&2 "AWS CLI is not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python 3 is not installed. Aborting."; exit 1; }

# Check if appsync-schema-uploader package is installed; install if necessary
if ! python3 -m pip show appsync-schema-uploader >/dev/null 2>&1; then
    echo "Installing appsync-schema-uploader..."
    python3 -m pip install appsync-schema-uploader
fi

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
