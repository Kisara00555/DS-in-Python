# System Architecture

## Main Classes

### DocumentProcessor

Loads PDF documents and extracts text.

### TextChunker

Splits extracted text into smaller chunks.

### EmbeddingManager

Generates vector embeddings from chunks.

### VectorStoreManager

Stores and retrieves embeddings using a vector database.

### RetrievalAgent

Retrieves the most relevant document chunks.

### LLMClient

Communicates with the Large Language Model.

### AnswerAgent

Generates final answers using retrieved context.

### Evaluator

Evaluates system answers against ground-truth answers.

## Pipeline

PDF Documents
→ DocumentProcessor
→ TextChunker
→ EmbeddingManager
→ VectorStoreManager
→ RetrievalAgent
→ LLMClient
→ AnswerAgent
→ Final Response
