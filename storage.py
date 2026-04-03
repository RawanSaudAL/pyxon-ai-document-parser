import os
import sqlite3
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "documents.db")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
COLLECTION_NAME = "document_chunks"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_client = None
_collection = None
_embedding_model = None


def ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def get_sql_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_sql_db() -> None:
    conn = get_sql_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            title TEXT,
            file_name TEXT,
            file_type TEXT,
            document_type TEXT,
            chunking_strategy TEXT,
            chunking_reason TEXT,
            chunk_count INTEGER,
            has_arabic INTEGER,
            has_diacritics INTEGER,
            language_label TEXT,
            text_length INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT,
            chunk_index INTEGER,
            text TEXT,
            length INTEGER,
            source_file TEXT,
            strategy TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (document_id)
        )
        """
    )

    conn.commit()
    conn.close()


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def initialize_vector_db():
    global _client, _collection

    ensure_data_dir()

    if _client is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )

    if _collection is None:
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)

    return _collection


def get_vector_collection():
    if _collection is None:
        return initialize_vector_db()
    return _collection


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()
    return embeddings


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def save_document_metadata(metadata: Dict[str, Any]) -> None:
    initialize_sql_db()

    conn = get_sql_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO documents (
            document_id,
            title,
            file_name,
            file_type,
            document_type,
            chunking_strategy,
            chunking_reason,
            chunk_count,
            has_arabic,
            has_diacritics,
            language_label,
            text_length
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metadata.get("document_id"),
            metadata.get("title"),
            metadata.get("file_name"),
            metadata.get("file_type"),
            metadata.get("document_type"),
            metadata.get("chunking_strategy"),
            metadata.get("chunking_reason"),
            int(metadata.get("chunk_count", 0)),
            int(bool(metadata.get("has_arabic"))),
            int(bool(metadata.get("has_diacritics"))),
            metadata.get("language_label"),
            int(metadata.get("text_length", 0)),
        ),
    )

    conn.commit()
    conn.close()


def save_document_chunks(document_id: str, chunk_records: List[Dict[str, Any]]) -> None:
    if not chunk_records:
        return

    initialize_sql_db()
    collection = get_vector_collection()

    conn = get_sql_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))

    texts = [record["text"] for record in chunk_records]
    embeddings = embed_texts(texts)
    ids = [record["chunk_id"] for record in chunk_records]

    metadatas = []
    for record in chunk_records:
        cur.execute(
            """
            INSERT OR REPLACE INTO chunks (
                chunk_id,
                document_id,
                chunk_index,
                text,
                length,
                source_file,
                strategy
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("chunk_id"),
                record.get("document_id"),
                int(record.get("chunk_index", 0)),
                record.get("text"),
                int(record.get("length", 0)),
                record.get("source_file"),
                record.get("strategy"),
            ),
        )

        metadatas.append(
            {
                "document_id": record.get("document_id"),
                "chunk_index": int(record.get("chunk_index", 0)),
                "length": int(record.get("length", 0)),
                "source_file": record.get("source_file", ""),
                "strategy": record.get("strategy", ""),
            }
        )

    try:
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    conn.commit()
    conn.close()


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    initialize_sql_db()

    conn = get_sql_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM documents WHERE document_id = ?",
        (document_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    result = row_to_dict(row)
    result["has_arabic"] = bool(result.get("has_arabic"))
    result["has_diacritics"] = bool(result.get("has_diacritics"))
    return result


def get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    initialize_sql_db()

    conn = get_sql_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT chunk_id, document_id, chunk_index, text, length, source_file, strategy, created_at
        FROM chunks
        WHERE document_id = ?
        ORDER BY chunk_index ASC
        """,
        (document_id,),
    )
    rows = cur.fetchall()
    conn.close()

    return [row_to_dict(row) for row in rows]


def get_all_documents() -> List[Dict[str, Any]]:
    initialize_sql_db()

    conn = get_sql_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM documents
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    documents = []
    for row in rows:
        item = row_to_dict(row)
        item["has_arabic"] = bool(item.get("has_arabic"))
        item["has_diacritics"] = bool(item.get("has_diacritics"))
        documents.append(item)

    return documents


def retrieve_relevant_chunks(query: str, document_id: Optional[str] = None, top_k: int = 4) -> List[Dict[str, Any]]:
    collection = get_vector_collection()

    query_embeddings = embed_texts([query])
    if not query_embeddings:
        return []

    query_embedding = query_embeddings[0]

    query_kwargs: Dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }

    if document_id:
        query_kwargs["where"] = {"document_id": document_id}

    results = collection.query(**query_kwargs)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    formatted_results = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        similarity_score = round(1 - float(distance), 4) if distance is not None else None
        formatted_results.append(
            {
                "text": text,
                "score": similarity_score,
                "document_id": metadata.get("document_id"),
                "chunk_index": metadata.get("chunk_index"),
                "length": metadata.get("length"),
                "source_file": metadata.get("source_file"),
                "strategy": metadata.get("strategy"),
            }
        )

    return formatted_results


def safe_int_to_bool(value: Any) -> bool:
    try:
        return bool(int(value))
    except Exception:
        return bool(value)


def answer_structured_query(document_id: str, question: str) -> str:
    document = get_document_by_id(document_id)
    if not document:
        return "Document metadata was not found."

    q = (question or "").strip().lower()

    if any(term in q for term in ["title", "document title", "عنوان", "العنوان", "اسم الموضوع", "اسم المستند"]):
        return f"Document title is {document.get('title', 'Unknown')}."

    if any(term in q for term in ["file type", "type of file", "نوع الملف", "امتداد"]):
        return f"File type is {document.get('file_type', 'Unknown')}."

    if any(term in q for term in ["document type", "نوع المستند", "نوع الوثيقة"]):
        return f"Document type is {document.get('document_type', 'Unknown')}."

    if any(term in q for term in ["chunk count", "how many chunks", "number of chunks", "عدد المقاطع", "عدد الأجزاء", "كم جزء"]):
        return f"The document was split into {document.get('chunk_count', 0)} chunks."

    if any(term in q for term in ["chunking strategy", "strategy", "طريقة التقسيم", "استراتيجية التقسيم"]):
        strategy = document.get("chunking_strategy", "Unknown")
        reason = document.get("chunking_reason", "")
        if reason:
            return f"Chunking strategy is {strategy}. Reason: {reason}"
        return f"Chunking strategy is {strategy}."

    if any(term in q for term in ["arabic", "عربي", "لغة عربية", "هل يحتوي عربي"]):
        value = safe_int_to_bool(document.get("has_arabic"))
        return "The document contains Arabic text." if value else "The document does not contain Arabic text."

    if any(term in q for term in ["diacritics", "harakat", "tashkeel", "تشكيل", "حركات"]):
        value = safe_int_to_bool(document.get("has_diacritics"))
        return "The document contains Arabic diacritics." if value else "The document does not contain Arabic diacritics."

    if any(term in q for term in ["language", "اللغة"]):
        return f"Language label is {document.get('language_label', 'Unknown')}."

    if any(term in q for term in ["file name", "filename", "اسم الملف"]):
        return f"File name is {document.get('file_name', 'Unknown')}."

    if any(term in q for term in ["reason", "سبب", "سبب اختيار", "سبب التقسيم"]):
        return document.get("chunking_reason", "No reason is available.")

    return (
        f"Available metadata: "
        f"title={document.get('title', 'Unknown')}, "
        f"file_type={document.get('file_type', 'Unknown')}, "
        f"chunk_count={document.get('chunk_count', 0)}"
    )