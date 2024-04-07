#!/bin/bash

# Define the response mapping template file
RESPONSE_TEMPLATE_FILE="response.vtl"

# Create the response mapping template file if it doesn't exist
if [ ! -f "$RESPONSE_TEMPLATE_FILE" ]; then
    echo '#if( $context.result && $context.result.error )
    $util.error($context.result.error.message)
#else
    $util.toJson($context.result)
#end' > "$RESPONSE_TEMPLATE_FILE"
fi

# Fetch all resolvers and their types
RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID" --query 'resolvers[*].[fieldName,typeName]' --output json)

# Loop over each resolver and update the response mapping template
for row in $(echo "${RESOLVERS}" | jq -r '.[] | @base64'); do
    _jq() {
        echo "${row}" | base64 --decode | jq -r "${1}"
    }

    RESOLVER_NAME=$(_jq '.[0]')
    TYPE_NAME=$(_jq '.[1]')

    if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --response-mapping-template "file://$RESPONSE_TEMPLATE_FILE"; then
        echo "Updated response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    else
        echo "Failed to update response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    fi
done

echo "Completed updating response mapping templates."
