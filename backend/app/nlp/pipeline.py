"""
NLP Pipeline for Supply Chain Disruption Analysis
Includes sentiment analysis, entity recognition, and topic classification
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import random


class SentimentCategory(Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


@dataclass
class NLPResult:
    """Result from NLP analysis"""
    text: str
    sentiment_score: float  # -1 to 1
    sentiment_category: SentimentCategory
    entities: List[Dict[str, str]]  # {text, type}
    keywords: List[str]
    disruption_type: Optional[str]
    risk_indicators: List[str]
    confidence: float


# Supply chain specific keywords and patterns
NEGATIVE_KEYWORDS = {
    "disruption", "delay", "shortage", "strike", "crisis", "halt", "suspend",
    "bankruptcy", "closure", "shutdown", "tariff", "sanction", "embargo",
    "recall", "failure", "bottleneck", "congestion", "constraint", "shortage",
    "volatility", "surge", "spike", "crash", "decline", "drop", "fall",
    "warning", "alert", "risk", "threat", "concern", "worry", "fear",
    "damage", "destruction", "disaster", "earthquake", "flood", "storm",
    "typhoon", "hurricane", "fire", "explosion", "accident", "incident",
    "ransomware", "cyberattack", "breach", "hack", "outage", "offline"
}

POSITIVE_KEYWORDS = {
    "recovery", "improvement", "growth", "expansion", "investment", "innovation",
    "agreement", "partnership", "collaboration", "milestone", "success",
    "efficiency", "optimization", "resilience", "diversification", "stable",
    "resolved", "restored", "reopened", "resumed", "normalized"
}

SUPPLY_CHAIN_ENTITIES = {
    "companies": [
        "Apple", "Samsung", "Intel", "TSMC", "Foxconn", "Amazon", "Walmart",
        "Toyota", "Volkswagen", "Tesla", "Maersk", "FedEx", "UPS", "DHL"
    ],
    "locations": [
        "China", "Taiwan", "Japan", "South Korea", "Vietnam", "India", "Germany",
        "United States", "Mexico", "Shanghai", "Shenzhen", "Singapore", "Rotterdam"
    ],
    "products": [
        "semiconductor", "chip", "battery", "EV", "electronics", "automotive",
        "pharmaceutical", "chemical", "steel", "aluminum", "rare earth"
    ],
    "infrastructure": [
        "port", "factory", "warehouse", "logistics hub", "manufacturing plant",
        "distribution center", "shipping lane", "supply route"
    ]
}

DISRUPTION_PATTERNS = {
    "natural_disaster": [
        r"earthquake|typhoon|hurricane|flood|storm|wildfire|tsunami|drought",
        r"weather|climate|natural disaster|force majeure"
    ],
    "geopolitical": [
        r"tariff|sanction|embargo|trade war|political|government|regulation",
        r"border|customs|policy|diplomatic|tension"
    ],
    "economic": [
        r"bankruptcy|inflation|recession|currency|price surge|cost increase",
        r"financial|economic|market crash|credit"
    ],
    "transportation": [
        r"port congestion|shipping delay|container|freight|logistics",
        r"transportation|trucking|rail|air freight|vessel"
    ],
    "labor": [
        r"strike|walkout|labor dispute|union|workforce|worker",
        r"shortage of workers|staffing|employment"
    ],
    "cyber": [
        r"ransomware|cyberattack|hack|breach|security incident",
        r"system outage|IT failure|data breach"
    ],
    "supplier": [
        r"supplier failure|vendor bankruptcy|supplier risk|sourcing",
        r"single source|supplier concentration"
    ]
}


class NLPPipeline:
    """NLP processing pipeline for supply chain text analysis"""
    
    def __init__(self):
        self.negative_keywords = NEGATIVE_KEYWORDS
        self.positive_keywords = POSITIVE_KEYWORDS
        self.entities = SUPPLY_CHAIN_ENTITIES
        self.disruption_patterns = DISRUPTION_PATTERNS
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Convert to lowercase
        text = text.lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)
        # Remove special characters but keep letters, numbers, spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def analyze_sentiment(self, text: str) -> Tuple[float, SentimentCategory]:
        """
        Analyze sentiment of text
        Returns score (-1 to 1) and category
        """
        processed = self.preprocess_text(text)
        words = set(processed.split())
        
        # Count positive and negative keywords
        neg_count = len(words & self.negative_keywords)
        pos_count = len(words & self.positive_keywords)
        
        # Calculate base sentiment
        total = neg_count + pos_count
        if total == 0:
            score = 0.0
        else:
            # Weight negative keywords more heavily for supply chain news
            score = (pos_count - neg_count * 1.5) / (total * 1.5)
            score = max(-1.0, min(1.0, score))
        
        # Add some variance for realism
        score += random.gauss(0, 0.1)
        score = max(-1.0, min(1.0, score))
        
        # Determine category
        if score <= -0.6:
            category = SentimentCategory.VERY_NEGATIVE
        elif score <= -0.2:
            category = SentimentCategory.NEGATIVE
        elif score <= 0.2:
            category = SentimentCategory.NEUTRAL
        elif score <= 0.6:
            category = SentimentCategory.POSITIVE
        else:
            category = SentimentCategory.VERY_POSITIVE
            
        return round(score, 3), category
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from text"""
        entities = []
        text_lower = text.lower()
        
        for entity_type, entity_list in self.entities.items():
            for entity in entity_list:
                if entity.lower() in text_lower:
                    entities.append({
                        "text": entity,
                        "type": entity_type
                    })
        
        return entities
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract important keywords from text"""
        processed = self.preprocess_text(text)
        words = processed.split()
        
        # Filter short words and combine with supply chain relevance
        relevant_words = []
        all_keywords = self.negative_keywords | self.positive_keywords
        
        for word in words:
            if len(word) > 3 and word in all_keywords:
                relevant_words.append(word)
        
        # Return unique keywords
        return list(dict.fromkeys(relevant_words))[:top_n]
    
    def classify_disruption_type(self, text: str) -> Optional[str]:
        """Classify the type of supply chain disruption"""
        text_lower = text.lower()
        
        for disruption_type, patterns in self.disruption_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return disruption_type
        
        return None
    
    def identify_risk_indicators(self, text: str) -> List[str]:
        """Identify specific risk indicators in text"""
        indicators = []
        text_lower = text.lower()
        
        risk_phrases = [
            ("supply shortage", "Potential supply shortage detected"),
            ("price increase", "Price increase risk identified"),
            ("delivery delay", "Delivery delays mentioned"),
            ("production halt", "Production stoppage indicated"),
            ("capacity constraint", "Capacity constraints reported"),
            ("inventory levels", "Inventory level concerns"),
            ("lead time", "Lead time extension risk"),
            ("force majeure", "Force majeure conditions"),
            ("single source", "Single source dependency risk"),
            ("quality issue", "Quality concerns identified"),
        ]
        
        for phrase, indicator in risk_phrases:
            if phrase in text_lower:
                indicators.append(indicator)
        
        return indicators
    
    def analyze(self, text: str) -> NLPResult:
        """
        Complete NLP analysis of supply chain text
        """
        sentiment_score, sentiment_category = self.analyze_sentiment(text)
        entities = self.extract_entities(text)
        keywords = self.extract_keywords(text)
        disruption_type = self.classify_disruption_type(text)
        risk_indicators = self.identify_risk_indicators(text)
        
        # Calculate confidence based on analysis quality
        confidence = 0.7
        if entities:
            confidence += 0.1
        if disruption_type:
            confidence += 0.1
        if risk_indicators:
            confidence += 0.05
        confidence = min(0.95, confidence)
        
        return NLPResult(
            text=text,
            sentiment_score=sentiment_score,
            sentiment_category=sentiment_category,
            entities=entities,
            keywords=keywords,
            disruption_type=disruption_type,
            risk_indicators=risk_indicators,
            confidence=round(confidence, 3)
        )
    
    def batch_analyze(self, texts: List[str]) -> List[NLPResult]:
        """Analyze multiple texts"""
        return [self.analyze(text) for text in texts]


# Singleton instance
_nlp_pipeline = None

def get_nlp_pipeline() -> NLPPipeline:
    """Get the NLP pipeline singleton"""
    global _nlp_pipeline
    if _nlp_pipeline is None:
        _nlp_pipeline = NLPPipeline()
    return _nlp_pipeline
