#!/bin/bash
# List all resolvers
RESOLVERS=$(aws appsync list-resolvers --api-id "$API_ID" --type-name "YourTypeName")
# Extract resolver names and type names
RESOLVER_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[] | .fieldName')
TYPE_NAMES=$(echo "$RESOLVERS" | jq -r '.resolvers[] | .typeName')
# Loop over resolver names and update request mapping template
while read -r RESOLVER_NAME && read -r TYPE_NAME <&3; do
  if aws appsync update-resolver --api-id "$API_ID" --type-name "$TYPE_NAME" --field-name "$RESOLVER_NAME" --request-mapping-template file://"$REQUEST_TEMPLATE_FILE"; then
    echo "Updated request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  else
    echo "Failed to update request mapping template for resolver $RESOLVER_NAME of type $TYPE_NAME."
  fi
done <<< "$RESOLVER_NAMES" 3<<< "$TYPE_NAMES"

echo "Completed updating request mapping templates."