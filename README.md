# Pyxon AI Document Parser

An AI-powered document parser designed for Retrieval-Augmented Generation (RAG) workflows.  
The system processes PDF, DOCX, and TXT files, analyzes document structure, automatically selects the most suitable chunking strategy, stores document data in both a Vector Database and a SQL Database, and supports Arabic text including diacritics.

## Live Demo
[Streamlit Demo](https://pyxon-ai-document-parser-ihajbesxfipgncvacu9imr.streamlit.app/)

## Project Overview
This project was built as part of the Pyxon AI Junior Engineer technical task.  
Its goal is to prepare uploaded documents for downstream RAG systems by combining document parsing, semantic understanding, intelligent chunking, metadata storage, and retrieval benchmarking.

The system supports:
- PDF files
- DOCX files
- TXT files
- Arabic and English text
- Arabic diacritics detection
- Semantic retrieval
- Structured metadata querying

## Features
- Multi-format document parsing for PDF, DOCX, and TXT
- Document structure analysis
- Automatic chunking strategy selection
- Fixed chunking for simple or uniform documents
- Dynamic chunking for structured or mixed-content documents
- Vector storage using ChromaDB
- SQL storage using SQLite
- Arabic language support including diacritics
- Semantic search over stored chunks
- Structured SQL-like metadata querying
- Benchmark suite for retrieval and performance evaluation
- Streamlit web demo for testing the system online

## System Architecture
The system is composed of four main layers:

### 1. Document Processing Layer
Handles file validation, text extraction, normalization, and language-aware preprocessing.

### 2. Document Understanding Layer
Analyzes structural properties such as:
- title
- paragraph count
- heading count
- bullet points
- numbered sections
- key concepts
- language type
- Arabic diacritics presence

### 3. Chunking Layer
Automatically chooses between:
- **Fixed chunking** for simple, uniform, or less-structured documents
- **Dynamic chunking** for documents with headings, sections, and variable structure

### 4. Storage and Retrieval Layer
- **SQLite** stores document metadata and chunk records
- **ChromaDB** stores vector embeddings for semantic retrieval
- **Sentence Transformers** generates multilingual embeddings

## End-to-End Workflow
1. Upload a document through the Streamlit interface
2. Validate file type
3. Extract raw text
4. Normalize text
5. Analyze document structure
6. Select chunking strategy automatically
7. Generate chunks
8. Store metadata in SQLite
9. Store chunk embeddings in ChromaDB
10. Query the document through:
   - semantic search
   - structured metadata queries
11. Evaluate retrieval quality using the benchmark module

## Intelligent Chunking Logic
The chunking strategy is selected automatically based on document analysis.

### Dynamic chunking is preferred when:
- multiple headings are detected
- structured sections or bullet patterns exist
- paragraph lengths suggest rich semantic structure

### Fixed chunking is preferred when:
- the document is short or simple
- paragraph boundaries are weak
- the content is more uniform

This makes the parser more adaptable than a single static chunking method.

## Storage Design

### SQL Database
SQLite is used to store:
- document ID
- title
- file name
- file type
- document type
- chunking strategy
- chunking reason
- language metadata
- Arabic and diacritics flags
- chunk count
- text length

### Vector Database
ChromaDB is used to store:
- chunk text
- chunk embeddings
- chunk metadata
- source file
- chunk index
- chunking strategy

This dual-storage design supports both:
- semantic retrieval
- structured metadata access

## Arabic Language Support
The system includes dedicated support for Arabic documents, including:
- Arabic text detection
- Arabic diacritics detection
- encoding-safe text extraction
- multilingual embedding generation
- Arabic retrieval benchmark cases

This makes the parser suitable for mixed-language and Arabic-first RAG workflows.

## Benchmarking
The project includes a benchmark suite to evaluate:
- retrieval hit rate
- answer accuracy
- average latency
- memory usage
- Arabic retrieval behavior
- Arabic diacritics retrieval behavior

Example benchmark output includes:
- total cases
- correct answers
- retrieval accuracy
- average latency
- category-level performance
- memory consumption

## Technology Stack
- **Frontend Demo:** Streamlit
- **Document Parsing:** PyPDF, python-docx
- **Embedding Model:** sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- **Vector Database:** ChromaDB
- **SQL Database:** SQLite
- **Language Processing:** custom utilities for Arabic and structure analysis

## Project Structure
```bash
.
├── app.py
├── benchmark.py
├── storage.py
├── utils.py
├── requirements.txt
└── README.md
