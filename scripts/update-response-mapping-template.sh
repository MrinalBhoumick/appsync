#!/bin/bash

# Create response.vtl file with the response mapping template content
echo '#if( $context.result && $context.result.error )
    $util.error($context.result.error.message)
#else
    $util.toJson($context.result)
#end' > response.vtl

RESPONSE_TEMPLATE_FILE="response.vtl"

# List all resolvers
RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID")
# Extract resolver names and type names
RESOLVER_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[].fieldName')
TYPE_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[].typeName')

# Loop over resolver names and update response mapping template
for RESOLVER_NAME in $RESOLVER_NAMES; do
  TYPE_NAME=$(echo "$RESOLVERS" | jq -r --arg RESOLVER_NAME "$RESOLVER_NAME" '.resolvers[] | select(.fieldName == $RESOLVER_NAME) | .typeName')
  if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --response-mapping-template file://"$RESPONSE_TEMPLATE_FILE"; then
    echo "Updated response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  else
    echo "Failed to update response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  fi
done

echo "Completed updating response mapping templates."
