import time
from typing import Any, Dict, List

import streamlit as st

from storage import (
    initialize_sql_db,
    initialize_vector_db,
    save_document_metadata,
    save_document_chunks,
    retrieve_relevant_chunks,
    answer_structured_query,
    get_all_documents,
    get_document_chunks,
)
from utils import (
    get_file_extension,
    validate_file,
    extract_text,
    normalize_text,
    analyze_document_structure,
    select_chunking_strategy,
    fixed_chunk_text,
    dynamic_chunk_text,
    build_chunk_records,
    generate_document_id,
)


def process_document(file_name: str, file_bytes: bytes) -> Dict[str, Any]:
    valid, error = validate_file(file_name)
    if not valid:
        raise ValueError(error)

    extracted_text = extract_text(file_name, file_bytes)
    cleaned_text = normalize_text(extracted_text)

    if not cleaned_text:
        raise ValueError("No extractable text was found in the uploaded document.")

    analysis = analyze_document_structure(cleaned_text, file_name)
    strategy, reason = select_chunking_strategy(analysis)

    if strategy == "dynamic":
        chunks = dynamic_chunk_text(cleaned_text)
    else:
        chunks = fixed_chunk_text(cleaned_text)

    if not chunks:
        raise ValueError("Chunking failed because no valid chunks were produced.")

    document_id = generate_document_id()
    file_type = get_file_extension(file_name).replace(".", "").upper()

    metadata = {
        "document_id": document_id,
        "title": analysis["title"],
        "file_name": file_name,
        "file_type": file_type,
        "document_type": analysis["document_type"],
        "chunking_strategy": strategy,
        "chunking_reason": reason,
        "chunk_count": len(chunks),
        "has_arabic": analysis["has_arabic"],
        "has_diacritics": analysis["has_diacritics"],
        "language_label": analysis["language_label"],
        "text_length": len(cleaned_text),
    }

    chunk_records = build_chunk_records(document_id, chunks, file_name, strategy)

    save_document_metadata(metadata)
    save_document_chunks(document_id, chunk_records)

    return {
        "document_id": document_id,
        "metadata": metadata,
        "analysis": analysis,
        "chunks": chunk_records,
        "raw_text": cleaned_text,
    }


def generate_simple_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    if not retrieved_chunks:
        return "No relevant answer was found."

    q = (query or "").strip().lower()

    combined_text = "\n".join(
        chunk.get("text", "").strip()
        for chunk in retrieved_chunks
        if chunk.get("text", "").strip()
    ).strip()

    if not combined_text:
        return "No relevant answer was found."

    lines = [line.strip() for line in combined_text.splitlines() if line.strip()]

    if any(term in q for term in ["عنوان", "العنوان", "title", "subject", "اسم الموضوع"]):
        for line in lines:
            lower_line = line.lower()
            if "العنوان" in line or "title" in lower_line:
                return line
        return lines[0] if lines else combined_text[:300]

    if any(term in q for term in ["ما موضوع", "موضوع", "about", "summary", "ملخص"]):
        return combined_text[:500]

    return combined_text[:500]


def render_document_overview(metadata: Dict[str, Any]) -> None:
    st.subheader("Document Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Language", metadata["language_label"])
    with col2:
        st.metric("Chunking Strategy", metadata["chunking_strategy"])
    with col3:
        st.metric("Total Chunks", metadata["chunk_count"])
    with col4:
        st.metric("Text Length", metadata["text_length"])

    st.write(f"**Title:** {metadata['title']}")
    st.write(f"**File Name:** {metadata['file_name']}")
    st.write(f"**File Type:** {metadata['file_type']}")
    st.write(f"**Document Type:** {metadata['document_type']}")


def render_document_analysis(analysis: Dict[str, Any]) -> None:
    st.subheader("Document Analysis")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Paragraph Count", analysis["paragraph_count"])
        st.metric("Average Paragraph Length", analysis["avg_paragraph_length"])
    with col2:
        st.metric("Heading Count", analysis["heading_count"])
        st.metric("List Count", analysis["bullet_points"])
    with col3:
        st.metric("Document Type", analysis["document_type"])
        st.metric("Lines", analysis["line_count"])

    st.write(f"**Language:** {analysis['language_label']}")
    st.write(f"**Has Arabic:** {analysis['has_arabic']}")
    st.write(f"**Has Diacritics:** {analysis['has_diacritics']}")

    if analysis["headings"]:
        st.write("**Topics**")
        for heading in analysis["headings"]:
            st.write(heading)

    if analysis["key_concepts"]:
        st.write("**Key Concepts**")
        for concept in analysis["key_concepts"]:
            st.write(concept)


def render_storage_summary(document_id: str, chunks: List[Dict[str, Any]]) -> None:
    st.subheader("Storage Summary")
    all_docs = get_all_documents()
    sql_chunks = get_document_chunks(document_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vector DB Count", len(chunks))
    with col2:
        st.metric("SQL Document Count", len(all_docs))
    with col3:
        st.metric("SQL Chunk Count", len(sql_chunks))


def render_structured_query(document_id: str) -> None:
    st.subheader("Structured SQL Query")
    prompt = st.text_input(
        "Ask a structured question about document metadata",
        placeholder="العنوان",
        key="structured_query",
    )

    if st.button("Run Structured Query", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter a structured question first.")
            return

        answer = answer_structured_query(document_id=document_id, question=prompt)
        st.write(answer)


def render_chunk_preview(chunks: List[Dict[str, Any]]) -> None:
    st.subheader("First Chunk Preview")
    if not chunks:
        st.write("No chunks available.")
        return

    st.write(chunks[0]["text"][:1200])


def render_semantic_search(document_id: str) -> None:
    st.subheader("Semantic Search")
    query = st.text_input("Ask a question about the document", key="semantic_query")

    if st.button("Search Semantically", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a question first.")
            return

        start = time.time()
        results = retrieve_relevant_chunks(query=query, document_id=document_id, top_k=4)
        elapsed = round(time.time() - start, 4)

        if not results:
            st.write("**Generated Answer**")
            st.write("No relevant answer was found.")
            return

        answer = generate_simple_answer(query, results)

        st.write("**Generated Answer**")
        st.write(answer)

        st.write("**Top Retrieved Chunks**")
        for idx, result in enumerate(results, start=1):
            with st.expander(f"Result #{idx}", expanded=(idx == 1)):
                st.write(f"**Document Name:** {result.get('source_file', '')}")
                st.write(f"**Chunk ID:** {result.get('chunk_index', '')}")
                st.write(f"**Strategy:** {result.get('strategy', '')}")
                st.write(f"**Length:** {result.get('length', '')}")
                if result.get("score") is not None:
                    st.write(f"**Score:** {result.get('score')}")
                st.write(result.get("text", ""))

        st.caption(f"Search completed in {elapsed} seconds.")


def render_processed_documents() -> None:
    docs = get_all_documents()
    if not docs:
        return

    st.subheader("Processed Documents")
    for doc in docs:
        st.write(
            f"- {doc.get('title', 'Untitled')} | "
            f"{doc.get('file_type', 'Unknown')} | "
            f"{doc.get('chunking_strategy', 'Unknown')} | "
            f"{doc.get('chunk_count', 0)} chunks"
        )


def initialize_app() -> None:
    initialize_sql_db()
    initialize_vector_db()

    if "processed_document" not in st.session_state:
        st.session_state.processed_document = None


def main() -> None:
    st.set_page_config(page_title="Pyxon AI Document Parser", layout="wide")
    initialize_app()

    st.title("Pyxon AI Document Parser")
    st.write(
        "Upload a PDF, DOCX, or TXT document, analyze its structure, choose an intelligent chunking strategy, "
        "store it in Vector and SQL databases, and retrieve the most relevant chunks for semantic search and answer generation."
    )
    st.write(
        "This demo supports Arabic and English documents. Some Arabic PDF files may contain rendering artifacts depending on the source PDF encoding."
    )

    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        if st.button("Process Document", use_container_width=True):
            try:
                result = process_document(uploaded_file.name, file_bytes)
                st.session_state.processed_document = result
                st.success("Document processed successfully.")
            except Exception as e:
                st.error(f"Processing failed: {e}")

    result = st.session_state.processed_document

    if result:
        metadata = result["metadata"]
        analysis = result["analysis"]
        chunks = result["chunks"]
        document_id = result["document_id"]

        render_document_overview(metadata)
        render_document_analysis(analysis)
        render_storage_summary(document_id, chunks)
        render_structured_query(document_id)
        render_chunk_preview(chunks)
        render_semantic_search(document_id)

    render_processed_documents()


if __name__ == "__main__":
    main()