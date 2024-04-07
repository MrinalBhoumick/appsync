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
RESOLVER_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[] | .fieldName')
TYPE_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[] | .typeName')

# Loop over resolver names and update response mapping template
while read -r RESOLVER_NAME && read -r TYPE_NAME <&3; do
  if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --response-mapping-template file://"$RESPONSE_TEMPLATE_FILE"; then
    echo "Updated response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  else
    echo "Failed to update response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  fi
done <<< "$RESOLVER_NAMES" 3<<< "$TYPE_NAMES"

echo "Completed updating response mapping templates."
