#!/bin/bash


# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python first."
    exit 1
fi

# Check if appsync-schema-uploader package is installed
if ! python -m pip show appsync-schema-uploader &> /dev/null; then
    echo "Installing appsync-schema-uploader..."
    python -m pip install appsync-schema-uploader
fi

# Configure AWS CLI if not already configured
if [[ ! -f ~/.aws/credentials ]]; then
    echo "AWS CLI is not configured. Configuring AWS CLI..."
    aws configure
fi

# Prompt the user to enter the AppSync API ID
read -p "Enter your AppSync API ID: " API_ID

# Check if the API ID is not empty
if [[ -z "$API_ID" ]]; then
    echo "API ID cannot be empty."
    exit 1
fi

# Determine the path to the templates directory relative to the script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TEMPLATES_DIR="$SCRIPT_DIR/../templates"  # Adjust relative path as needed
SCHEMA_FILE="$TEMPLATES_DIR/data.graphql"

# Check if the schema file exists and is not empty
if [[ ! -s $SCHEMA_FILE ]]; then
    echo "Schema file not found or is empty: $SCHEMA_FILE"
    exit 1
fi

# Update the AppSync API schema using appsync-schema-uploader
echo "Updating AppSync API schema..."
python -m appsync_schema_uploader \
    --api-id "$API_ID" \
    --schema "$SCHEMA_FILE"

echo "Schema update process completed."
