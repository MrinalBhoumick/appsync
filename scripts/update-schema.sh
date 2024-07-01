#!/bin/bash

# Fetch AppSync API ID from the environment
if [[ -z "$API_ID" ]]; then
    echo "Error: API_ID environment variable is not set."
    exit 1
fi

# Determine the path to the templates directory relative to the script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TEMPLATES_DIR="$SCRIPT_DIR/../templates"
SCHEMA_FILE="$TEMPLATES_DIR/data.graphql"

# Check if the schema file exists and is not empty
if [[ ! -s $SCHEMA_FILE ]]; then
    echo "Error: Schema file not found or is empty: $SCHEMA_FILE"
    exit 1
fi

# Encode the GraphQL schema file in base64
SCHEMA_BASE64=$(base64 -w 0 "$SCHEMA_FILE")

# Assume the role and get temporary credentials
ASSUME_ROLE_OUTPUT=$(aws sts assume-role --role-arn arn:aws:iam::058264356572:role/sts-tenant-lambda-role --role-session-name CodeBuildSession)
export AWS_ACCESS_KEY_ID=$(echo $ASSUME_ROLE_OUTPUT | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo $ASSUME_ROLE_OUTPUT | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo $ASSUME_ROLE_OUTPUT | jq -r '.Credentials.SessionToken')

# Initiate schema creation for the AppSync API
echo "Updating AppSync API schema..."
aws appsync start-schema-creation --api-id "$API_ID" --definition "data:text/plain;base64,$SCHEMA_BASE64"

echo "Schema update process completed."
