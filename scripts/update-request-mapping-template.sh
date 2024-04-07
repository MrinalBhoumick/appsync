#!/bin/bash

# List all types from the schema
TYPES=$(aws appsync list-types --api-id "$API_ID")

# Extract type names
TYPE_NAMES=$(echo "$TYPES" | jq -r '.types[].name')

# Loop over type names and update request mapping template
for TYPE_NAME in $TYPE_NAMES; do
  # Check if the type name is a resolver type
  if [[ "$TYPE_NAME" == *"ResolverType"* ]]; then
    if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --request-mapping-template file://"$REQUEST_TEMPLATE_FILE"; then
      echo "Updated request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    else
      echo "Failed to update request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
    fi
  fi
done

echo "Completed updating request mapping templates."
