#!/bin/bash

# Check and install required dependencies
check_dependencies() {
    # Check for yq
    if ! command -v yq &> /dev/null; then
        echo "yq is not installed. Installing..."
        sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq
        sudo chmod +x /usr/bin/yq
    fi

    # Check for jq
    if ! command -v jq &> /dev/null; then
        echo "jq is not installed. Installing..."
        sudo apt-get update && sudo apt-get install -y jq
    fi

    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo "curl is not installed. Installing..."
        sudo apt-get update && sudo apt-get install -y curl
    fi
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOC_FILE="${SCRIPT_DIR}/../api_documentation.md"

# Base URL
BASE_URL="http://localhost:8000"

# Run dependency check before main execution
check_dependencies

# Check if server is running
check_server() {
    echo "Checking if txtai server is running..."
    if ! curl -s \
        -H "Authorization: Bearer ${API_KEY}" \
        "${BASE_URL}/openapi.json" > /dev/null; then
        echo -e "${RED}Error: txtai server is not running at ${BASE_URL}${NC}"
        echo "Please start the server using the handler.sh script first"
        exit 1
    fi
    echo -e "${GREEN}Server is running!${NC}"
}

# Format JSON with truncation
format_json() {
    local json=$1
    local max_items=${2:-10}

    if [[ $json == "["* ]]; then
        if echo "$json" | jq -e 'all(type == "number")' > /dev/null; then
            echo "$json" | jq --argjson max "$max_items" '
                if length > $max then
                    .[:$max] + ["...(truncated)"]
                else
                    .
                end'
        else
            echo "$json" | jq '.'
        fi
    else
        echo "$json" | jq '.'
    fi
}

# Function to format description text
format_description() {
    local desc=$1
    # Split Args and Returns into separate lines, format as bullet points
    echo "$desc" | sed 's/Args:/\n\nArgs:\n/g' | \
                   sed 's/Returns:/\n\nReturns:\n/g' | \
                   sed 's/\. /.\n/g' | \
                   sed 's/Args:\n\([^R]*\)/Args:\n\1/' | \
                   sed 's/^- /  - /g'
}

# Function to get clean description from OpenAPI spec
get_clean_description() {
    local endpoint_spec=$1
    local desc=$(echo "$endpoint_spec" | jq -r '.description // empty')

    if [[ ! -z "$desc" ]]; then
        format_description "$desc"
    else
        echo "No description available"
    fi
}

# Function to clean parameter text
clean_parameter() {
    local param=$1
    echo "$param" | sed 's/  */ /g' | sed 's/ \+/ /g'
}

# Function to resolve schema reference
resolve_schema() {
    local spec=$1
    local schema=$2

    # Check if schema has a $ref
    if [[ $(echo "$schema" | jq 'has("$ref")') == "true" ]]; then
        local ref=$(echo "$schema" | jq -r '."$ref"')
        # Remove the #/components/schemas/ prefix
        ref=${ref#"#/components/schemas/"}
        # Get the actual schema
        echo "$spec" | jq -r --arg ref "$ref" '.components.schemas[$ref]'
    else
        echo "$schema"
    fi
}

# Function to format JSON schema
format_schema() {
    local schema=$1
    # Format JSON consistently without extra quotes/commas
    echo "$schema" | \
        jq 'del(..|nulls)' | \
        jq '.' | \
        # Remove trailing commas
        sed 's/,\s*}/}/g' | \
        sed 's/,\s*\]/]/g'
}

# Function to document POST request schema
document_post_schema() {
    local endpoint_spec=$1
    local spec=$2
    local path=$3

    # Get schema from endpoint spec
    local schema=$(echo "$endpoint_spec" | jq -r '.requestBody.content["application/json"].schema')

    # If no schema found, generate based on endpoint
    if [[ -z "$schema" || "$schema" == "null" ]]; then
        case "$path" in
            "/batchsearch")
                schema='{
  "type": "object",
  "properties": {
    "queries": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of search queries"
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of results per query"
    }
  },
  "required": ["queries"]
}'
                ;;
            "/batchsimilarity")
                schema='{
  "type": "object",
  "properties": {
    "queries": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of queries to compare"
    },
    "texts": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of texts to compare against"
    }
  },
  "required": ["queries", "texts"]
}'
                ;;
            "/batchsegment"|"/batchtransform")
                schema='{
  "type": "array",
  "items": {
    "type": "string"
  },
  "description": "List of texts to process"
}'
                ;;
            "/explain"|"/batchexplain")
                schema='{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Query text"
    },
    "texts": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of texts to analyze"
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of results"
    }
  },
  "required": ["query", "texts"]
}'
                ;;
        esac
    fi

    if [[ ! -z "$schema" && "$schema" != "null" ]]; then
        schema=$(resolve_schema "$spec" "$schema")
        echo -e "\n**Request Body Schema:**" >> "${DOC_FILE}"
        echo "\`\`\`json" >> "${DOC_FILE}"
        format_schema "$schema" >> "${DOC_FILE}"
        echo "\`\`\`" >> "${DOC_FILE}"
    fi
}

# Function to create GitHub-compatible anchor
create_anchor() {
    local text=$1
    # Convert to lowercase, replace slashes and special chars with hyphens
    echo "$text" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/-\+/-/g' | sed 's/^-\|-$//'
}

# Function to document response schema
document_response_schema() {
    local endpoint_spec=$1
    local spec=$2
    local path=$3

    echo -e "\n**Response Schema:**" >> "${DOC_FILE}"
    echo "\`\`\`json" >> "${DOC_FILE}"

    # Determine response type based on endpoint path and description
    case "$path" in
        "/search"|"/batchsearch"|"/similarity"|"/batchsimilarity")
            echo '{
  "results": [
    {
      "id": "doc1",
      "score": 0.95
    },
    {
      "id": "doc2",
      "score": 0.85
    }
  ]
}' >> "${DOC_FILE}"
            ;;
        "/transform"|"/batchtransform")
            echo '{
  "embeddings": [0.1, 0.2, 0.3, 0.4, 0.5]
}' >> "${DOC_FILE}"
            ;;
        "/segment"|"/batchsegment")
            echo '{
  "segments": [
    "First semantic unit.",
    "Second semantic unit.",
    "Third semantic unit."
  ]
}' >> "${DOC_FILE}"
            ;;
        "/explain"|"/batchexplain")
            echo '{
  "results": [
    {
      "token": "example",
      "score": 0.8,
      "text": "example text"
    },
    {
      "token": "text",
      "score": 0.6,
      "text": "example text"
    }
  ]
}' >> "${DOC_FILE}"
            ;;
        "/count")
            echo '{
  "count": 42
}' >> "${DOC_FILE}"
            ;;
        "/add"|"/addimage"|"/addobject"|"/delete"|"/index"|"/upsert"|"/reindex")
            echo '{
  "success": true,
  "message": "Operation completed successfully"
}' >> "${DOC_FILE}"
            ;;
        *)
            # Get response schema from OpenAPI spec
            local schema=$(echo "$endpoint_spec" | jq -r '.responses["200"].content["application/json"].schema')
            if [[ ! -z "$schema" && "$schema" != "null" ]]; then
                schema=$(resolve_schema "$spec" "$schema")
                format_schema "$schema" >> "${DOC_FILE}"
            else
                echo '{
  "success": true
}' >> "${DOC_FILE}"
            fi
            ;;
    esac

    echo "\`\`\`" >> "${DOC_FILE}"
}

# Function to document an endpoint
document_endpoint() {
    local path=$1
    local method=$2
    local spec=$3
    local config=$4

    local endpoint_spec=$(echo "$spec" | jq --arg path "$path" --arg method "${method,,}" '.paths[$path][$method]')

    # Get availability based on config
    local status="Available"
    case "$path" in
        "/add"|"/delete"|"/update")
            [[ "$(echo "$config" | yq .writable)" != "true" ]] && status="Requires writable: true"
            ;;
        "/similarity"|"/search")
            [[ -z "$(echo "$config" | yq .embeddings.path)" ]] && status="Requires embeddings configuration"
            ;;
    esac

    # Write documentation header
    cat >> "${DOC_FILE}" << EOF

### ${path}
- **Method:** ${method^^}
- **Status:** ${status}
EOF

    # Document request/response types
    if [[ "${method,,}" == "post" ]]; then
        echo -e "\n- **Request:**\n\`\`\`typescript" >> "${DOC_FILE}"
        get_typescript_interface "$endpoint_spec" "request" "$path" >> "${DOC_FILE}"
        echo -e "\`\`\`" >> "${DOC_FILE}"
    fi

    # Add GET parameters documentation
    if [[ "${method,,}" == "get" ]]; then
        case "$path" in
            "/search"|"/segment"|"/transform")
                echo -e "\n- **Parameters:**\n\`\`\`typescript" >> "${DOC_FILE}"
                case "$path" in
                    "/search")
                        echo "interface Params {
  query: string;  // Search query text
}" >> "${DOC_FILE}"
                        ;;
                    "/segment")
                        echo "interface Params {
  text: string;  // Text to segment into sentences
}" >> "${DOC_FILE}"
                        ;;
                    "/transform")
                        echo "interface Params {
  text: string;       // Text to transform into vector
  category?: string;  // Optional category
  index?: string;     // Optional index name
}" >> "${DOC_FILE}"
                        ;;
                esac
                echo -e "\`\`\`" >> "${DOC_FILE}"
                ;;
        esac
    fi

    # Document response type
    echo -e "\n- **Response:**\n\`\`\`typescript" >> "${DOC_FILE}"
    get_typescript_interface "$endpoint_spec" "response" "$path" >> "${DOC_FILE}"
    echo -e "\`\`\`" >> "${DOC_FILE}"

    # Add example
    echo -e "\n- **Example:**\n\`\`\`javascript" >> "${DOC_FILE}"
    generate_example "$path" "$method" "$endpoint_spec" >> "${DOC_FILE}"
    echo -e "\`\`\`" >> "${DOC_FILE}"
}

# Function to document GET parameters
document_get_params() {
    local endpoint_spec=$1
    local params=$(echo "$endpoint_spec" | jq -r '.parameters[]? |
        "- `" + .name + "`: " + (.description // "Parameter description not available") +
        " (" + (if .required then "required" else "optional" end) + ")\n" +
        "  - Type: `" + (.schema.type // "string") + "`" +
        (if .schema.example then "\n  - Example: `" + (.schema.example|tostring) + "`" else "" end) +
        (if .schema.default then "\n  - Default: `" + (.schema.default|tostring) + "`" else "" end)')

    if [[ ! -z "$params" ]]; then
        echo -e "\n**Parameters:**" >> "${DOC_FILE}"
        echo "$params" >> "${DOC_FILE}"
    fi
}

# Function to document endpoints
document_endpoints() {
    local spec=$1
    local config=$2
    local paths=($(echo "$spec" | jq -r '.paths | keys[]' | sort))

    # First generate TOC
    echo "## Table of Contents" >> "${DOC_FILE}"
    for path in "${paths[@]}"; do
        local anchor=$(create_anchor "$path")
        echo "- [\`${path}\`](#${anchor})" >> "${DOC_FILE}"
    done
    echo "" >> "${DOC_FILE}"

    # Then document each endpoint
    for path in "${paths[@]}"; do
        local method=$(echo "$spec" | jq -r --arg path "$path" '.paths[$path] | keys[0]')
        document_endpoint "$path" "${method^^}" "$spec" "$config"
    done
}

# Function to check endpoint availability based on config
is_endpoint_available() {
    local path=$1
    local config=$2

    case "$path" in
        "/add"|"/delete"|"/update")
            [[ "$(echo "$config" | yq .writable)" == "true" ]] && echo "Always available" || echo "Requires writable: true in config"
            ;;
        "/similarity"|"/search")
            [[ -n "$(echo "$config" | yq .embeddings.path)" ]] && echo "Always available" || echo "Requires embeddings configuration"
            ;;
        *)
            echo "Always available"
            ;;
    esac
}

# Function to generate example request
generate_example() {
    local path=$1
    local method=$2
    local endpoint_spec=$3

    case "$path" in
        "/add")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, [
  {text: 'text1', id: 'id1', tags: {key: 'value'}},  // tags optional
  {text: 'text2', id: 'id2'}
]);"
            ;;
        "/delete")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, [
  'id1',
  'id2'
]);"
            ;;
        "/search")
            echo "const response = await axios.get(\`\${API_BASE}${path}\`, {
  params: {
    query: 'search query'
  }
});"
            ;;
        "/segment")
            echo "const response = await axios.get(\`\${API_BASE}${path}\`, {
  params: {
    text: 'text to segment'
  }
});"
            ;;
        "/transform")
            echo "const response = await axios.get(\`\${API_BASE}${path}\`, {
  params: {
    text: 'text to transform',
    category: 'optional category',  // optional
    index: 'optional index'        // optional
  }
});"
            ;;
        "/batchsegment"|"/batchtransform")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  texts: ['text to process 1', 'text to process 2']
});"
            ;;
        "/similarity")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  query: 'similarity query',
  texts: ['text to compare 1', 'text to compare 2']
});"
            ;;
        "/reindex")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  config: {
    path: 'new-embeddings-model',
    dimension: 384
  }
});"
            ;;
        "/delete")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  ids: ['id1', 'id2']
});"
            ;;
        # POST endpoints with specific schemas
        "/add")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  texts: ['text1', 'text2'],
  ids: ['id1', 'id2'],  // optional
  tags: [{key: 'value'}]  // optional
});"
            ;;
        "/addimage"|"/addobject")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  data: [/* binary data */],
  uid: ['id1', 'id2'],
  field: 'content'  // optional
});"
            ;;
        "/batchsearch")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  queries: ['query1', 'query2'],
  limit: 10
});"
            ;;
        "/batchsimilarity")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  queries: ['query1', 'query2'],
  texts: ['text1', 'text2', 'text3']
});"
            ;;
        "/explain"|"/batchexplain")
            echo "const response = await axios.post(\`\${API_BASE}${path}\`, {
  query: 'search query',
  texts: ['text1', 'text2'],
  limit: 5
});"
            ;;
        # Simple GET endpoints
        "/count"|"/index"|"/upsert")
            echo "const response = await axios.get(\`\${API_BASE}${path}\`);"
            ;;
        # Default case
        *)
            if [[ "${method,,}" == "post" ]]; then
                echo "const response = await axios.post(\`\${API_BASE}${path}\`, {});"
            else
                echo "const response = await axios.get(\`\${API_BASE}${path}\`);"
            fi
            ;;
    esac
}

# Update get_typescript_interface to handle null schemas
get_typescript_interface() {
    local spec=$1
    local type=$2
    local path=$3

    case "$type" in
        "request")
            case "$path" in
                "/add")
                    echo "type Request = Array<{
  text: string;          // Document text content
  id: string;           // Unique document identifier
  tags?: {             // Optional metadata tags
    [key: string]: any;
  };
}>"
                    ;;
                "/delete")
                    echo "type Request = string[]  // Array of document IDs to delete"
                    ;;
                "/batchsearch")
                    echo "interface Request {
  queries: string[];    // Array of search queries
  limit?: number;      // Optional max results per query
}"
                    ;;
                "/similarity")
                    echo "interface Request {
  query: string;       // Text to compare against
  texts: string[];     // Array of texts to compare with query
}"
                    ;;
                "/explain"|"/batchexplain")
                    echo "interface Request {
  query: string;       // Search/analysis query
  texts: string[];     // Texts to analyze
  limit?: number;      // Optional max results
}"
                    ;;
                "/transform"|"/batchtransform")
                    echo "interface Request {
  texts: string[];     // Texts to convert to vectors
}"
                    ;;
                *)
                    echo "interface Request {
  // See API documentation for request parameters
}"
                    ;;
            esac
            ;;
        "response")
            case "$path" in
                "/search"|"/similarity"|"/batchsearch")
                    if [[ "$path" == "/batchsearch" ]]; then
                        echo "type Response = Array<Array<{
  id: string;           // Document ID
  score: number;       // Similarity/relevance score
}>>"
                    else
                        echo "type Response = Array<{
  id: string;           // Document ID
  score: number;       // Similarity/relevance score
}>"
                    fi
                    ;;
                "/transform"|"/batchtransform")
                    if [[ "$path" == "/batchtransform" ]]; then
                        echo "type Response = Array<number[]>  // Array of vector representations"
                    else
                        echo "type Response = number[]  // Vector representation"
                    fi
                    ;;
                "/segment"|"/batchsegment")
                    echo "interface Response {
  segments: string[];    // Array of text segments
}"
                    ;;
                "/explain"|"/batchexplain")
                    echo "interface Response {
  results: Array<{
    id: number;        // Result index
    text: string;      // Original text
    score: number;     // Overall score
    tokens: Array<[string, number]>;  // Token scores
  }>;
}"
                    ;;
                "/count")
                    echo "type Response = number  // Number of indexed documents"
                    ;;
                "/add"|"/delete"|"/index"|"/upsert")
                    if [[ "$path" == "/delete" ]]; then
                        echo "type Response = string[]  // Array of deleted document IDs"
                    else
                        echo "type Response = null"
                    fi
                    ;;
                *)
                    echo "interface Response {
  success: boolean;
  message?: string;
}"
                    ;;
            esac
            ;;
    esac
}

# Main execution
main() {
    check_server

    # Get OpenAPI spec once
    local spec=$(curl -s "${BASE_URL}/openapi.json")

    # Parse config.yml
    local config=$(cat "${SCRIPT_DIR}/../config/config.yml")

    # Initialize documentation file
    cat > "${DOC_FILE}" << EOF
# txtai API Documentation
Generated on: $(date '+%Y-%m-%d %H:%M:%S')

## Base URL: ${BASE_URL}

## Authentication
All endpoints require an API key to be passed in the Authorization header:
\`\`\`
Authorization: Bearer ${API_KEY}
\`\`\`

## Configuration Status
The following features are currently enabled based on config.yml:
- Writable API: $([ "$(echo "$config" | yq .writable)" == "true" ] && echo "✅" || echo "❌")
- Embeddings: $([ -n "$(echo "$config" | yq .embeddings.path)" ] && echo "✅ ($(echo "$config" | yq .embeddings.path))" || echo "❌")
- Index Backend: $(echo "$config" | yq .index.backend)
- Text Segmentation: $([ "$(echo "$config" | yq .segmentation.sentences)" == "true" ] && echo "✅" || echo "❌")
- Authentication: ✅ (API Key Required)

EOF

    # Document all endpoints
    document_endpoints "$spec" "$config"
}

# Call main function
main

echo "API documentation has been saved to ${DOC_FILE}"