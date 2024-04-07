#!/bin/bash

# Create response.vtl file with the response mapping template content
echo '#if( $context.result && $context.result.error )
    $util.error($context.result.error.message)
#else
    $util.toJson($context.result)
#end' > response.vtl

RESPONSE_TEMPLATE_FILE="response.vtl"

# Fetch the schema definition
SCHEMA=$(aws appsync get-introspection-schema --api-id "$API_ID" --format SDL)

# Extract resolver type name
RESOLVER_TYPE_NAME=$(echo "$SCHEMA" | grep -oP 'type \K\w+' | grep ResolverType)

# List all resolvers of the resolver type
RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID" --type-name "$RESOLVER_TYPE_NAME")
RESOLVER_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[].fieldName')

# Loop over resolver names and update response mapping template
for RESOLVER_NAME in $RESOLVER_NAMES; do
  if aws appsync update-resolver --api-id "$API_ID" --type-name "$RESOLVER_TYPE_NAME" --field-name "$RESOLVER_NAME" --response-mapping-template "file://$RESPONSE_TEMPLATE_FILE"; then
    echo "Updated response mapping template for resolver $RESOLVER_NAME of type $RESOLVER_TYPE_NAME."
  else
    echo "Failed to update response mapping template for resolver $RESOLVER_NAME of type $RESOLVER_TYPE_NAME."
  fi
done

echo "Completed updating response mapping templates."
