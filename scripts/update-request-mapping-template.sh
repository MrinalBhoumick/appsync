#!/bin/bash
REQUEST_TEMPLATE_FILE="request.vtl"

# List all types from the schema
TYPES=$(aws appsync list-types --api-id "$API_ID")

# Extract type names
TYPE_NAMES=$(echo "$TYPES" | jq -r '.types[] | select(.definition | startswith("type")) | .name')

# Loop over type names and update request mapping template for each resolver
for TYPE_NAME in $TYPE_NAMES; do
  RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID" --type-name "$TYPE_NAME")
  RESOLVER_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[] | .fieldName')
  
  # Loop over resolver names and update request mapping template
  while read -r RESOLVER_NAME; do
    if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --request-mapping-template file://"$REQUEST_TEMPLATE_FILE"; then
      echo "Updated request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    else
      echo "Failed to update request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    fi
  done <<< "$RESOLVER_NAMES"
done

echo "Completed updating request mapping templates."
