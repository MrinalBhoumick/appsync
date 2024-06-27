#!/bin/bash

# Ensure API_ID is set before running this script
# Set the path to the request mapping template file
REQUEST_TEMPLATE_FILE="templates/request_mapping.graphql"

echo "Updating request mapping templates for resolvers in AppSync API with API ID $API_ID"

# Fetch all resolvers and their types
RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID" --query 'resolvers[*].[fieldName,typeName]' --output json)

# Check if RESOLVERS is empty
if [ -z "$RESOLVERS" ]; then
    echo "No resolvers found for API ID $API_ID."
    exit 1
fi

# Loop over each resolver and update the request mapping template
for row in $(echo "${RESOLVERS}" | jq -r '.[] | @base64'); do
    _jq() {
        echo "${row}" | base64 --decode | jq -r "${1}"
    }

    RESOLVER_NAME=$(_jq '.[0]')
    TYPE_NAME=$(_jq '.[1]')

    echo "Updating resolver: $RESOLVER_NAME of type $TYPE_NAME"

    if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --request-mapping-template "file://$REQUEST_TEMPLATE_FILE"; then
        echo "Updated request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    else
        echo "Failed to update request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    fi
done

echo "Completed updating request mapping templates."
