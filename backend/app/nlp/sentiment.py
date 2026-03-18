"""
Sentiment Analyser — FIX 5 stub / FIX 18 FinBERT implementation
Uses HuggingFace ProsusAI/finbert when available, falls back to keyword-based scoring.
"""
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Supply-chain disruption keywords for score amplification
DISRUPTION_AMPLIFIERS = {
    "port strike": 0.15,
    "shortage": 0.12,
    "recall": 0.10,
    "sanctions": 0.12,
    "embargo": 0.14,
    "blockade": 0.15,
    "ransomware": 0.13,
    "bankruptcy": 0.12,
    "shutdown": 0.10,
    "congestion": 0.08,
    "tariff": 0.08,
    "supply disruption": 0.14,
    "force majeure": 0.15,
    "natural disaster": 0.13,
}


class SentimentAnalyzer:
    """
    Supply-chain sentiment analyser.
    When transformers is available: uses ProsusAI/finbert for financial sentiment.
    Otherwise: falls back to keyword-based scoring from the existing NLP pipeline.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self._pipeline = None
        self._model_name = model_name
        self._use_transformer = False
        self._load_model()

    def _load_model(self):
        """Attempt to load HuggingFace model."""
        try:
            from transformers import pipeline as hf_pipeline

            self._pipeline = hf_pipeline(
                "sentiment-analysis",
                model=self._model_name,
                tokenizer=self._model_name,
                truncation=True,
                max_length=512,
            )
            self._use_transformer = True
            logger.info(f"✅ FinBERT loaded: {self._model_name}")
        except ImportError:
            logger.info("transformers not installed — using keyword-based sentiment")
        except Exception as e:
            logger.warning(f"Failed to load FinBERT: {e} — using keyword-based sentiment")

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text.
        Returns: {score: float (-1 to 1), label: str, confidence: float}
        """
        if self._use_transformer and self._pipeline:
            return self._transformer_analyze(text)
        return self._keyword_analyze(text)

    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts (FIX 18: batch inference support)."""
        if self._use_transformer and self._pipeline:
            return self._transformer_batch(texts)
        return [self._keyword_analyze(t) for t in texts]

    # ---- Transformer path ----

    def _transformer_analyze(self, text: str) -> Dict:
        """FinBERT single inference with supply-chain amplification."""
        try:
            result = self._pipeline(text[:512])[0]
            label = result["label"].lower()  # positive / negative / neutral
            raw_score = result["score"]

            # Map to -1..1 scale
            if label == "negative":
                score = -raw_score
            elif label == "positive":
                score = raw_score
            else:
                score = 0.0

            # Supply-chain keyword amplification (FIX 18)
            score = self._apply_amplifiers(text, score)

            return {
                "score": round(max(-1.0, min(1.0, score)), 3),
                "label": label,
                "confidence": round(raw_score, 3),
                "model": self._model_name,
            }
        except Exception as e:
            logger.warning(f"FinBERT inference failed: {e}")
            return self._keyword_analyze(text)

    def _transformer_batch(self, texts: List[str]) -> List[Dict]:
        """FinBERT batch inference."""
        try:
            truncated = [t[:512] for t in texts]
            results = self._pipeline(truncated)
            output = []
            for i, result in enumerate(results):
                label = result["label"].lower()
                raw_score = result["score"]

                if label == "negative":
                    score = -raw_score
                elif label == "positive":
                    score = raw_score
                else:
                    score = 0.0

                score = self._apply_amplifiers(texts[i], score)
                output.append({
                    "score": round(max(-1.0, min(1.0, score)), 3),
                    "label": label,
                    "confidence": round(raw_score, 3),
                    "model": self._model_name,
                })
            return output
        except Exception as e:
            logger.warning(f"FinBERT batch failed: {e}")
            return [self._keyword_analyze(t) for t in texts]

    # ---- Keyword fallback path ----

    def _keyword_analyze(self, text: str) -> Dict:
        """TextBlob fallback sentiment analysis."""
        try:
            from textblob import TextBlob
            score = TextBlob(text).sentiment.polarity
            label = "neutral"
            if score >= 0.1:
                label = "positive"
            elif score <= -0.1:
                label = "negative"
            # Apply supply-chain amplifiers
            score = self._apply_amplifiers(text, float(score))
                
            return {
                "score": float(round(max(-1.0, min(1.0, score)), 3)),
                "label": label,
                "confidence": 0.8,
                "model": "textblob_fallback",
            }
        except ImportError:
            logger.warning("textblob not installed — returning neutral sentiment")
            return {
                "score": 0.0,
                "label": "neutral",
                "confidence": 0.1,
                "model": "stub_fallback"
            }

    # ---- Amplifiers ----

    def _apply_amplifiers(self, text: str, score: float) -> float:
        """Amplify negative sentiment for supply-chain disruption keywords."""
        text_lower = text.lower()
        for keyword, boost in DISRUPTION_AMPLIFIERS.items():
            if keyword in text_lower:
                # Push sentiment more negative when disruption keywords present
                score -= boost
        return score


# Singleton
_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
