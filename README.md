# Pyxon AI Document Parser – Technical Task Submission

---

## Summary
This project is an AI-powered document parser designed for Retrieval-Augmented Generation (RAG) workflows. It processes PDF, DOCX, and TXT files, analyzes document structure, automatically selects the optimal chunking strategy, and stores data in both a Vector Database and a SQL Database.

The system supports multilingual content, including Arabic with diacritics, and provides both semantic search and structured querying capabilities. A full benchmarking suite is included to evaluate retrieval accuracy, latency, and system performance.

---

## Contact Information
📧 Email: rawa.431rawan@gmail.com  or rawan.s.alahmadi1@gmail.com
📱 Phone: 966 553097668  
## Live Demo
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
The system follows a modular architecture:

1. Processing Layer → extraction + normalization  
2. Understanding Layer → structure + language analysis  
3. Chunking Layer → adaptive (fixed / dynamic)  
4. Storage Layer → SQLite + ChromaDB  
5. Retrieval Layer → semantic + structured queries  

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

```bash
git clone https://github.com/RawanSaudAL/pyxon-ai-document-parser.git
cd pyxon-ai-document-parser
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
