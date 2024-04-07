#!/bin/bash

# List all types from the schema
TYPES=$(aws appsync list-types --api-id "$API_ID")

# Extract resolver type names
RESOLVER_TYPE_NAMES=$(echo "$TYPES" | jq -r '.types[] | select(.definition | test("type ResolverType")) | .name')

# Loop over resolver type names and update request mapping template
for TYPE_NAME in $RESOLVER_TYPE_NAMES; do
  RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID" --type-name "$TYPE_NAME")
  RESOLVER_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[].fieldName')
  while IFS= read -r RESOLVER_NAME; do
    if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --request-mapping-template file://"$REQUEST_TEMPLATE_FILE"; then
      echo "Updated request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    else
      echo "Failed to update request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    fi
  done <<< "$RESOLVER_NAMES"
done

echo "Completed updating request mapping templates."
