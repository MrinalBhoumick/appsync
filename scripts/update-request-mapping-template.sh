#!/bin/bash

# List all types from the schema
TYPES=$(aws appsync list-types --api-id "$API_ID")

# Extract resolver names and type names
RESOLVER_NAMES=$(echo "$TYPES" | jq -r '.types[] | select(.definition | contains("type ResolverType")) | .name')
TYPE_NAMES=$(echo "$TYPES" | jq -r '.types[] | select(.definition | contains("type ResolverType")) | .name')

# Loop over resolver names and update request mapping template
while IFS= read -r RESOLVER_NAME && IFS= read -r TYPE_NAME; do
  if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --request-mapping-template file://"$REQUEST_TEMPLATE_FILE"; then
    echo "Updated request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  else
    echo "Failed to update request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  fi
done < <(paste <(printf "%s\n" "$RESOLVER_NAMES") <(printf "%s\n" "$TYPE_NAMES"))

echo "Completed updating request mapping templates."
