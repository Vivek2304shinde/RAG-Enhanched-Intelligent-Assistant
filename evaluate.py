# evaluate.py
import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from src.agents.runner import run_agent
from src.utils.logging import logger

# Sample benchmark (replace with actual human‑verified data)
benchmark = [
    {
        "question": "What is the current repo rate?",
        "ground_truth": "The repo rate is 6.5% as of June 2024."
    },
    # ... add 50+ examples
]

async def evaluate_rag():
    questions = [item["question"] for item in benchmark]
    ground_truths = [item["ground_truth"] for item in benchmark]
    answers = []
    contexts = []  # we'll collect retrieved chunks

    for q in questions:
        result = run_agent(q)
        answers.append(result["answer"])
        # Retrieve contexts from state (we need to modify runner to return them)
        # For now, we'll simulate by calling retrieval pipeline separately
        from src.retrieval.retrieval_pipeline import retrieval_pipeline
        chunks = retrieval_pipeline.retrieve(q)
        contexts.append([c["text"] for c in chunks[:3]])

    # Build dataset
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)
    score = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall, context_precision])
    logger.info(f"Evaluation scores: {score}")
    return score

if __name__ == "__main__":
    asyncio.run(evaluate_rag())