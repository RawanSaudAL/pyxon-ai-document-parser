import json
import os
import re
import time
import tracemalloc
from typing import Any, Dict, List

from utils import (
    normalize_text,
    contains_arabic,
    contains_diacritics,
)
from storage import (
    get_all_documents,
    get_document_chunks,
    retrieve_relevant_chunks,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_OUTPUT_PATH = os.path.join(BASE_DIR, "benchmark_results.json")


def normalize_for_match(text: str) -> str:
    text = normalize_text(text or "")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def evaluate_hit(retrieved_docs: List[str], expected_keyword: str) -> bool:
    if not expected_keyword:
        return False

    normalized_expected = normalize_for_match(expected_keyword)
    for doc in retrieved_docs:
        if normalized_expected in normalize_for_match(doc):
            return True
    return False


def benchmark_retrieval_case(case: Dict[str, Any]) -> Dict[str, Any]:
    query = case["query"]
    expected_keyword = case["expected_keyword"]
    document_id = case.get("document_id")
    top_k = case.get("top_k", 3)

    start_time = time.time()
    results = retrieve_relevant_chunks(query=query, document_id=document_id, top_k=top_k)
    latency = round(time.time() - start_time, 4)

    retrieved_docs = [item.get("text", "") for item in results]
    hit = evaluate_hit(retrieved_docs, expected_keyword)

    return {
        "query": query,
        "expected_keyword": expected_keyword,
        "document_id": document_id,
        "top_k": top_k,
        "hit": hit,
        "latency_seconds": latency,
        "retrieved_count": len(retrieved_docs),
        "preview": retrieved_docs[0][:220] if retrieved_docs else "",
    }


def benchmark_memory_and_time(retrieval_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    tracemalloc.start()
    start = time.time()

    results = []
    for case in retrieval_cases:
        results.append(benchmark_retrieval_case(case))

    elapsed = round(time.time() - start, 4)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "execution_time_seconds": elapsed,
        "current_memory_mb": round(current / (1024 * 1024), 4),
        "peak_memory_mb": round(peak / (1024 * 1024), 4),
        "cases_run": len(results),
    }


def get_default_benchmark_cases() -> List[Dict[str, Any]]:
    documents = get_all_documents()
    if not documents:
        return []

    cases = []

    for doc in documents[:3]:
        document_id = doc["document_id"]
        chunks = get_document_chunks(document_id)
        if not chunks:
            continue

        first_chunk = chunks[0]["text"]
        words = first_chunk.split()
        expected_keyword = " ".join(words[:8]).strip() if len(words) >= 8 else first_chunk[:40].strip()

        title = doc.get("title", "Untitled")
        has_arabic = bool(doc.get("has_arabic", False))
        has_diacritics = bool(doc.get("has_diacritics", False))

        cases.append(
            {
                "query": f"What is this document about: {title}?",
                "expected_keyword": expected_keyword,
                "document_id": document_id,
                "top_k": 3,
                "category": "retrieval_answering",
            }
        )

        if has_arabic:
            arabic_probe = expected_keyword if contains_arabic(expected_keyword) else first_chunk[:80]
            cases.append(
                {
                    "query": "ما موضوع هذا المستند؟",
                    "expected_keyword": arabic_probe,
                    "document_id": document_id,
                    "top_k": 3,
                    "category": "arabic_test",
                }
            )

        if has_diacritics:
            diacritic_probe = next(
                (token for token in first_chunk.split() if contains_diacritics(token)),
                first_chunk[:60],
            )
            cases.append(
                {
                    "query": "هل يمكنك استرجاع نص يحتوي على تشكيل؟",
                    "expected_keyword": diacritic_probe,
                    "document_id": document_id,
                    "top_k": 3,
                    "category": "diacritics_test",
                }
            )

    return cases


def summarize_cases(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not case_results:
        return {
            "total_cases": 0,
            "correct_answers": 0,
            "answer_accuracy": 0,
            "retrieval_hit_rate": 0,
            "average_latency": 0,
            "category_summary": {},
        }

    total_cases = len(case_results)
    correct_answers = sum(1 for case in case_results if case["hit"])
    answer_accuracy = round((correct_answers / total_cases) * 100, 2) if total_cases else 0
    retrieval_hit_rate = answer_accuracy
    average_latency = round(
        sum(case["latency_seconds"] for case in case_results) / total_cases, 4
    ) if total_cases else 0

    category_bucket: Dict[str, Dict[str, int]] = {}
    for case in case_results:
        category = case.get("category", "general")
        if category not in category_bucket:
            category_bucket[category] = {"total": 0, "correct": 0}
        category_bucket[category]["total"] += 1
        if case["hit"]:
            category_bucket[category]["correct"] += 1

    category_summary = {}
    for category, stats in category_bucket.items():
        total = stats["total"]
        correct = stats["correct"]
        score = round((correct / total) * 100, 2) if total else 0
        category_summary[category] = {
            "accuracy_percent": score,
            "correct": correct,
            "total": total,
        }

    return {
        "total_cases": total_cases,
        "correct_answers": correct_answers,
        "answer_accuracy": answer_accuracy,
        "retrieval_hit_rate": retrieval_hit_rate,
        "average_latency": average_latency,
        "category_summary": category_summary,
    }


def save_benchmark_results(results: Dict[str, Any], output_path: str = BENCHMARK_OUTPUT_PATH) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def run_full_benchmark(custom_cases: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    cases = custom_cases if custom_cases is not None else get_default_benchmark_cases()

    if not cases:
        results = {
            "status": "no_documents",
            "message": "No processed documents were found. Please upload and process at least one document before running the benchmark.",
            "summary": {
                "total_cases": 0,
                "correct_answers": 0,
                "answer_accuracy": 0,
                "retrieval_hit_rate": 0,
                "average_latency": 0,
            },
            "case_results": [],
        }
        save_benchmark_results(results)
        return results

    case_results = []
    for case in cases:
        result = benchmark_retrieval_case(case)
        result["category"] = case.get("category", "general")
        case_results.append(result)

    summary = summarize_cases(case_results)
    performance = benchmark_memory_and_time(cases)

    results = {
        "status": "completed",
        "summary": summary,
        "performance": performance,
        "case_results": case_results,
    }

    save_benchmark_results(results)
    return results


def print_benchmark_report(results: Dict[str, Any]) -> None:
    print("\n========== FINAL RESULTS ==========\n")

    summary = results.get("summary", {})
    category_summary = summary.get("category_summary", {})

    print(f"Total Cases: {summary.get('total_cases', 0)}")
    print(f"Correct Answers: {summary.get('correct_answers', 0)}")
    print(f"Answer Accuracy: {summary.get('answer_accuracy', 0):.2f}%")
    print(f"Retrieval Hit Rate: {summary.get('retrieval_hit_rate', 0):.2f}%")
    print(f"Average Latency: {summary.get('average_latency', 0):.4f} sec")

    print("\nCategory Summary:")
    for category, stats in category_summary.items():
        print(f"- {category}: {stats['accuracy_percent']:.2f}% ({stats['correct']}/{stats['total']})")

    print(f"\nBenchmark report saved to {BENCHMARK_OUTPUT_PATH}")
    print("\n========== BENCHMARK END ==========\n")


if __name__ == "__main__":
    benchmark_results = run_full_benchmark()
    print_benchmark_report(benchmark_results)