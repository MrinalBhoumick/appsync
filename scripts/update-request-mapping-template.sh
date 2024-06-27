#!/bin/bash

API_ID="6o2znoypyjdthf6vdtf6rhwnz4"  # Replace with your actual API ID
AWS_REGION="ap-south-1"  # Replace with your AWS region

# Check if there are any resolvers to update
resolver_count=$(aws appsync list-resolvers --api-id $API_ID --query "length(resolvers)" --output text --region $AWS_REGION)

if [ $resolver_count -eq 0 ]; then
    echo "No resolvers found for API ID $API_ID."
    exit 0  # Exit gracefully as there's nothing to update
fi

# Iterate over each resolver and update the request mapping template
resolvers=$(aws appsync list-resolvers --api-id $API_ID --query "resolvers[*].typeName" --output text --region $AWS_REGION)

for resolver in $resolvers; do
    echo "Updating request mapping template for resolver: $resolver"
    aws appsync update-resolver --api-id $API_ID --type-name $resolver --field-name <FIELD_NAME> --request-mapping-template file://$GITHUB_WORKSPACE/templates/request-mapping-template.graphql --region $AWS_REGION
done

echo "Request mapping templates updated successfully for all resolvers."
