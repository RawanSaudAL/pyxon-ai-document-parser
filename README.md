## Summary
This project is an AI-powered document parser designed for Retrieval-Augmented Generation (RAG) workflows. It processes PDF, DOCX, and TXT files, analyzes document structure, automatically selects the optimal chunking strategy, and stores data in both a Vector Database and a SQL Database.

The system supports multilingual content, including Arabic with diacritics, and provides both semantic search and structured querying capabilities. A full benchmarking suite is included to evaluate retrieval accuracy, latency, and system performance.

---

## Contact Information
📧 Email: rawa.431rawan@gmail.com  
📱 Phone: [Add if you want]  

---

## Demo Link
🔗 https://pyxon-ai-document-parser-ihajbesxfipgncvacu9imr.streamlit.app/

---

## Features Implemented
- [x] Document parsing (PDF, DOCX, TXT)
- [x] Content analysis and chunking strategy selection
- [x] Fixed and dynamic chunking
- [x] Vector DB integration (ChromaDB)
- [x] SQL DB integration (SQLite)
- [x] Arabic language support
- [x] Arabic diacritics support
- [x] Benchmark suite
- [x] RAG integration ready

---

## Architecture
The system follows a modular architecture composed of:

1. **Processing Layer**  
   Handles file validation, text extraction, and normalization.

2. **Understanding Layer**  
   Analyzes document structure (headings, paragraphs, patterns, language).

3. **Chunking Layer**  
   Automatically selects:
   - Fixed chunking for simple documents  
   - Dynamic chunking for structured documents  

4. **Storage Layer**  
   - SQLite for structured metadata  
   - ChromaDB for semantic vector storage  

5. **Retrieval Layer**  
   Supports both:
   - Semantic search using embeddings  
   - Structured querying via SQL  

---

## Technologies Used
- Python  
- Streamlit  
- Sentence Transformers  
- ChromaDB  
- SQLite  
- PyPDF  
- python-docx  

---

## Benchmark Results
- Total Cases: 6  
- Correct Answers: 6  
- Answer Accuracy: 100.00%  
- Retrieval Hit Rate: 100.00%  
- Average Latency: 0.1141 sec  
- Arabic Support: Yes  
- Diacritics Support: Yes  

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/RawanSaudAL/pyxon-ai-document-parser.git
cd pyxon-ai-document-parser
