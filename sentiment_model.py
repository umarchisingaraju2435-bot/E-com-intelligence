from transformers import pipeline
import os

_classifier = None

def _load():
    global _classifier
    if _classifier is None:
        print("⏳ Loading BERT sentiment model (first time may take a minute)...")
        _classifier = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            truncation=True,
            max_length=512
        )
        print("✅ BERT model loaded.")

def predict(text):
    """Returns 'positive' or 'negative' for a single review text."""
    _load()
    result = _classifier(text[:512])[0]
    # model returns 1-5 stars: 1-2 = negative, 3 = neutral→negative, 4-5 = positive
    stars = int(result["label"][0])
    return "positive" if stars >= 4 else "negative"

def predict_proba(text):
    """Returns confidence score (0.0 to 1.0) for positive sentiment."""
    _load()
    result = _classifier(text[:512])[0]
    stars  = int(result["label"][0])
    score  = result["score"]
    return round(score if stars >= 4 else 1 - score, 2)

def analyze_reviews(review_texts):
    """
    Takes a list of review strings.
    Returns:
        positive: list of positive reviews
        negative: list of negative reviews
        score:    overall sentiment score (0-100)
    """
    _load()
    positive = []
    negative = []
    for review in review_texts:
        if not review.strip():
            continue
        label = predict(review)
        if label == "positive":
            positive.append(review)
        else:
            negative.append(review)

    total = len(positive) + len(negative)
    score = round((len(positive) / total) * 100) if total > 0 else 50
    return positive, negative, score

def is_model_ready():
    """BERT is always ready — no pre-training needed."""
    return True
