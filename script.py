import re
import csv

# File paths
input_file = 'templates/data.graphql'
output_file = 'Query-Mutation-List.csv'

# Templates
query_response_template = "Response Mapping Template 1"
mutation_response_template = "Response Mapping Template 2"

# Regular expressions to match Queries and Mutations
query_pattern = re.compile(r'type Query \{([^}]+)\}', re.DOTALL)
mutation_pattern = re.compile(r'type Mutation \{([^}]+)\}', re.DOTALL)
operation_pattern = re.compile(r'(\w+)\s*\(.*')

def extract_operations(schema, pattern):
    match = pattern.search(schema)
    if not match:
        return []
    operations_block = match.group(1)
    operations = operation_pattern.findall(operations_block)
    return operations

def read_schema(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_csv(file_path, queries, mutations):
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write the header for the Query table
        writer.writerow(['Queries', 'Request Template', 'Response Template'])
        # Write the Query operations
        for query in queries:
            writer.writerow([query, 'Updated', query_response_template])

        # Write an empty row to separate tables
        writer.writerow([])

        # Write the header for the Mutation table
        writer.writerow(['Mutations', 'Request Template', 'Response Template'])
        # Write the Mutation operations
        for mutation in mutations:
            writer.writerow([mutation,'Updated', mutation_response_template])

# Main execution
schema = read_schema(input_file)
queries = extract_operations(schema, query_pattern)
mutations = extract_operations(schema, mutation_pattern)

write_csv(output_file, queries, mutations)

print(f'CSV file {output_file} has been created successfully.')
