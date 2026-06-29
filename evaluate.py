# evaluate.py
import asyncio
import tempfile
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from src.agents.runner import run_agent
from src.speech.asr import asr
from src.speech.tts import tts
from src.retrieval.retrieval_pipeline import retrieval_pipeline
from src.utils.logging import logger
import jiwer
import time

# -------------------- RAG Evaluation --------------------
async def evaluate_rag():
    logger.info("Starting RAG evaluation...")
    # Sample benchmark – replace with actual 50+ examples
    benchmark = [
        {"question": "What is the repo rate?", "ground_truth": "The repo rate is 6.5%"},
        {"question": "Which ministry implements PMEGP?", "ground_truth": "Ministry of MSME"}
    ]
    questions = [b["question"] for b in benchmark]
    ground_truths = [b["ground_truth"] for b in benchmark]
    answers = []
    contexts = []
    for q in questions:
        result = run_agent(q)
        answers.append(result["answer"])
        # Get contexts from retrieval pipeline
        chunks = retrieval_pipeline.retrieve(q)
        contexts.append([c["text"] for c in chunks[:3]])
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)
    score = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall, context_precision])
    logger.info(f"RAG scores: {score}")
    return score

# -------------------- ASR Evaluation (WER) --------------------
def evaluate_asr():
    logger.info("Starting ASR evaluation...")
    # Use sample audio files if available; we'll simulate with a few test samples.
    # For real evaluation, you'd have a dataset of audio-transcript pairs.
    test_samples = [
        ("What are the RBI guidelines for MSME lending?", "What are the RBI guidelines for MSME lending?"),
        ("Tell me about the Union Budget 2024.", "Tell me about the Union Budget 2024.")
    ]
    total_wer = 0.0
    for audio_text, expected in test_samples:
        # Simulate audio bytes from text (we just call TTS then ASR back)
        audio_bytes = tts.synthesize(audio_text)
        transcript = asr.transcribe(audio_bytes)
        wer = jiwer.wer(expected, transcript)
        total_wer += wer
        logger.info(f"WER for '{audio_text}': {wer:.2f}")
    avg_wer = total_wer / len(test_samples)
    logger.info(f"Average WER: {avg_wer:.2f}")
    return avg_wer

# -------------------- TTS Evaluation (Latency) --------------------
def evaluate_tts():
    logger.info("Starting TTS evaluation...")
    test_text = "This is a test of the text-to-speech system."
    start = time.time()
    audio_bytes = tts.synthesize(test_text)
    latency = time.time() - start
    logger.info(f"TTS latency: {latency:.2f}s for {len(test_text)} chars")
    # Also check audio length? Not necessary for demo.
    return latency

# -------------------- Main --------------------
if __name__ == "__main__":
    # Run RAG evaluation
    rag_scores = asyncio.run(evaluate_rag())
    print("\nRAG Evaluation Results:", rag_scores)
    
    # Run ASR evaluation
    wer = evaluate_asr()
    print("ASR WER:", wer)
    
    # Run TTS evaluation
    latency = evaluate_tts()
    print("TTS Latency:", latency)