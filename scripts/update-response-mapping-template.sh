#!/bin/bash

RESPONSE_TEMPLATE_FILE="response.vtl"

# Create response.vtl file with the response mapping template content
echo '#if( $context.result && $context.result.error )
    $util.error($context.result.error.message)
#else
    $util.toJson($context.result)
#end' > "$RESPONSE_TEMPLATE_FILE"

# Fetch the schema definition
SCHEMA=$(aws appsync get-introspection-schema --api-id "$API_ID" --format SDL)

# Extract resolver type name
RESOLVER_TYPE_NAME=$(echo "$SCHEMA" | grep -oP 'type \K\w+' | grep ResolverType)

# List all resolvers of the resolver type
RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID" --type-name "$RESOLVER_TYPE_NAME" --query 'resolvers[*].[fieldName,typeName]' --output text)

while IFS=$'\t' read -r RESOLVER_NAME TYPE_NAME; do
  if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --response-mapping-template "file://$RESPONSE_TEMPLATE_FILE"; then
    echo "Updated response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  else
    echo "Failed to update response mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  fi
done <<< "$RESOLVERS"

echo "Completed updating response mapping templates."
