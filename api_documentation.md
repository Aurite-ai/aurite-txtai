# txtai API Documentation
Generated on: 2024-11-08 22:41:11

## Base URL: http://localhost:8000

## Authentication
All endpoints require an API key to be passed in the Authorization header:
```
Authorization: Bearer 
```

## Configuration Status
The following features are currently enabled based on config.yml:
- Writable API: ❌
- Embeddings: ✅ (sentence-transformers/all-MiniLM-L6-v2)
- Index Backend: annoy
- Text Segmentation: ✅
- Authentication: ✅ (API Key Required)

## Table of Contents
- [`/add`](#add)
- [`/addimage`](#addimage)
- [`/addobject`](#addobject)
- [`/batchexplain`](#batchexplain)
- [`/batchsearch`](#batchsearch)
- [`/batchsegment`](#batchsegment)
- [`/batchsimilarity`](#batchsimilarity)
- [`/batchtransform`](#batchtransform)
- [`/count`](#count)
- [`/delete`](#delete)
- [`/explain`](#explain)
- [`/index`](#index)
- [`/reindex`](#reindex)
- [`/search`](#search)
- [`/segment`](#segment)
- [`/similarity`](#similarity)
- [`/transform`](#transform)
- [`/upsert`](#upsert)


### /add
- **Method:** POST
- **Status:** Requires writable: true

- **Request:**
```typescript
type Request = Array<{
  text: string;          // Document text content
  id: string;           // Unique document identifier
  tags?: {             // Optional metadata tags
    [key: string]: any;
  };
}>
```

- **Response:**
```typescript
type Response = null
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/add`, [
  {text: 'text1', id: 'id1', tags: {key: 'value'}},  // tags optional
  {text: 'text2', id: 'id2'}
]);
```

### /addimage
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  // See API documentation for request parameters
}
```

- **Response:**
```typescript
interface Response {
  success: boolean;
  message?: string;
}
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/addimage`, {
  data: [/* binary data */],
  uid: ['id1', 'id2'],
  field: 'content'  // optional
});
```

### /addobject
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  // See API documentation for request parameters
}
```

- **Response:**
```typescript
interface Response {
  success: boolean;
  message?: string;
}
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/addobject`, {
  data: [/* binary data */],
  uid: ['id1', 'id2'],
  field: 'content'  // optional
});
```

### /batchexplain
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  query: string;       // Search/analysis query
  texts: string[];     // Texts to analyze
  limit?: number;      // Optional max results
}
```

- **Response:**
```typescript
interface Response {
  results: Array<{
    id: number;        // Result index
    text: string;      // Original text
    score: number;     // Overall score
    tokens: Array<[string, number]>;  // Token scores
  }>;
}
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/batchexplain`, {
  query: 'search query',
  texts: ['text1', 'text2'],
  limit: 5
});
```

### /batchsearch
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  queries: string[];    // Array of search queries
  limit?: number;      // Optional max results per query
}
```

- **Response:**
```typescript
type Response = Array<Array<{
  id: string;           // Document ID
  score: number;       // Similarity/relevance score
}>>
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/batchsearch`, {
  queries: ['query1', 'query2'],
  limit: 10
});
```

### /batchsegment
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  // See API documentation for request parameters
}
```

- **Response:**
```typescript
interface Response {
  segments: string[];    // Array of text segments
}
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/batchsegment`, {
  texts: ['text to process 1', 'text to process 2']
});
```

### /batchsimilarity
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  // See API documentation for request parameters
}
```

- **Response:**
```typescript
interface Response {
  success: boolean;
  message?: string;
}
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/batchsimilarity`, {
  queries: ['query1', 'query2'],
  texts: ['text1', 'text2', 'text3']
});
```

### /batchtransform
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  texts: string[];     // Texts to convert to vectors
}
```

- **Response:**
```typescript
type Response = Array<number[]>  // Array of vector representations
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/batchtransform`, {
  texts: ['text to process 1', 'text to process 2']
});
```

### /count
- **Method:** GET
- **Status:** Available

- **Response:**
```typescript
type Response = number  // Number of indexed documents
```

- **Example:**
```javascript
const response = await axios.get(`${API_BASE}/count`);
```

### /delete
- **Method:** POST
- **Status:** Requires writable: true

- **Request:**
```typescript
type Request = string[]  // Array of document IDs to delete
```

- **Response:**
```typescript
type Response = string[]  // Array of deleted document IDs
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/delete`, [
  'id1',
  'id2'
]);
```

### /explain
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  query: string;       // Search/analysis query
  texts: string[];     // Texts to analyze
  limit?: number;      // Optional max results
}
```

- **Response:**
```typescript
interface Response {
  results: Array<{
    id: number;        // Result index
    text: string;      // Original text
    score: number;     // Overall score
    tokens: Array<[string, number]>;  // Token scores
  }>;
}
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/explain`, {
  query: 'search query',
  texts: ['text1', 'text2'],
  limit: 5
});
```

### /index
- **Method:** GET
- **Status:** Available

- **Response:**
```typescript
type Response = null
```

- **Example:**
```javascript
const response = await axios.get(`${API_BASE}/index`);
```

### /reindex
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  // See API documentation for request parameters
}
```

- **Response:**
```typescript
interface Response {
  success: boolean;
  message?: string;
}
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/reindex`, {
  config: {
    path: 'new-embeddings-model',
    dimension: 384
  }
});
```

### /search
- **Method:** GET
- **Status:** Available

- **Parameters:**
```typescript
interface Params {
  query: string;  // Search query text
}
```

- **Response:**
```typescript
type Response = Array<{
  id: string;           // Document ID
  score: number;       // Similarity/relevance score
}>
```

- **Example:**
```javascript
const response = await axios.get(`${API_BASE}/search`, {
  params: {
    query: 'search query'
  }
});
```

### /segment
- **Method:** GET
- **Status:** Available

- **Parameters:**
```typescript
interface Params {
  text: string;  // Text to segment into sentences
}
```

- **Response:**
```typescript
interface Response {
  segments: string[];    // Array of text segments
}
```

- **Example:**
```javascript
const response = await axios.get(`${API_BASE}/segment`, {
  params: {
    text: 'text to segment'
  }
});
```

### /similarity
- **Method:** POST
- **Status:** Available

- **Request:**
```typescript
interface Request {
  query: string;       // Text to compare against
  texts: string[];     // Array of texts to compare with query
}
```

- **Response:**
```typescript
type Response = Array<{
  id: string;           // Document ID
  score: number;       // Similarity/relevance score
}>
```

- **Example:**
```javascript
const response = await axios.post(`${API_BASE}/similarity`, {
  query: 'similarity query',
  texts: ['text to compare 1', 'text to compare 2']
});
```

### /transform
- **Method:** GET
- **Status:** Available

- **Parameters:**
```typescript
interface Params {
  text: string;       // Text to transform into vector
  category?: string;  // Optional category
  index?: string;     // Optional index name
}
```

- **Response:**
```typescript
type Response = number[]  // Vector representation
```

- **Example:**
```javascript
const response = await axios.get(`${API_BASE}/transform`, {
  params: {
    text: 'text to transform',
    category: 'optional category',  // optional
    index: 'optional index'        // optional
  }
});
```

### /upsert
- **Method:** GET
- **Status:** Available

- **Response:**
```typescript
type Response = null
```

- **Example:**
```javascript
const response = await axios.get(`${API_BASE}/upsert`);
```
