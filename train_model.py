"""
Run this file ONCE to train and save your sentiment model.
    python3 train_model.py
"""

import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ── Built-in Dataset (no download needed) ────────────────────────────────────
# Real e-commerce style reviews — no SSL, no internet needed
POSITIVE_REVIEWS = [
    "excellent product highly recommended",
    "amazing quality worth every penny",
    "best purchase i have ever made",
    "superb quality fast delivery",
    "love this product works perfectly",
    "great value for money very happy",
    "outstanding performance exceeded expectations",
    "perfect product exactly as described",
    "very good quality satisfied with purchase",
    "fantastic product will buy again",
    "brilliant quality highly satisfied",
    "wonderful product great packaging",
    "top quality product fast shipping",
    "very happy with this purchase",
    "excellent build quality durable",
    "good product works as expected",
    "nice design comfortable to use",
    "great product no complaints",
    "solid product good value",
    "impressive quality for the price",
    "really good product recommend to everyone",
    "works great very satisfied",
    "high quality product love it",
    "perfect fit exactly what i needed",
    "amazing product five stars",
    "very durable and well made",
    "great customer service fast delivery",
    "product is exactly as advertised",
    "very pleased with this item",
    "good quality sturdy and reliable",
    "excellent item quick delivery",
    "happy with the purchase good quality",
    "works perfectly as described",
    "very well made product",
    "great product easy to use",
    "love the quality of this product",
    "best value for money",
    "highly recommend this product",
    "very satisfied with the quality",
    "good sturdy product works well",
    "nice product good packaging",
    "excellent quality fast shipping",
    "very good product as described",
    "great item satisfied customer",
    "product works perfectly happy",
    "good quality product recommend",
    "very happy fast delivery good quality",
    "excellent product great price",
    "amazing value highly recommend",
    "perfect product great quality",
    "superb item very happy with purchase",
    "great quality product no issues",
    "very good item works as expected",
    "love this item great quality",
    "excellent purchase very satisfied",
    "good product fast delivery happy",
    "wonderful quality great value",
    "top notch product highly recommend",
    "very impressed with quality",
    "great product solid build",
    "nice quality product satisfied",
    "excellent item great packaging",
    "very good quality recommend",
    "happy with purchase works great",
    "good value product satisfied",
    "great quality fast shipping",
    "love the product excellent quality",
    "very satisfied excellent product",
    "good product great price",
    "excellent quality very happy",
    "amazing product great value",
    "perfect item highly recommend",
    "very good product love it",
    "great purchase satisfied customer",
    "excellent item works perfectly",
    "good quality durable product",
    "very happy with this product",
    "great product excellent quality",
    "love it works perfectly",
    "very good value for money",
    "excellent product satisfied",
    "good item fast delivery",
    "great quality product love it",
    "very satisfied with purchase",
    "excellent value great product",
    "amazing quality product",
    "perfect purchase very happy",
    "good product highly recommend",
    "great item excellent quality",
    "very good product satisfied",
    "excellent purchase great value",
    "love this product recommend",
    "good quality fast shipping",
    "great product works well",
    "very happy excellent quality",
    "satisfied with purchase good product",
    "excellent item very good quality",
    "great value product recommend",
    "very good purchase satisfied",
    "good product excellent value",
    "love the quality recommend",
    "great product very satisfied",
]

NEGATIVE_REVIEWS = [
    "terrible product waste of money",
    "very poor quality not recommended",
    "broke after one day useless",
    "worst purchase ever disappointed",
    "bad quality do not buy",
    "completely useless poor quality",
    "very disappointed not as described",
    "cheap quality broke immediately",
    "awful product waste of money",
    "not worth the price poor quality",
    "terrible quality very unhappy",
    "bad product poor packaging",
    "slow delivery damaged product",
    "very poor quality disappointed",
    "not as advertised bad quality",
    "waste of money terrible product",
    "poor quality broke quickly",
    "very bad product not recommended",
    "disappointed with quality poor",
    "cheap and nasty poor quality",
    "bad purchase regret buying",
    "very slow delivery poor quality",
    "not worth it bad product",
    "terrible experience poor quality",
    "broken on arrival very disappointed",
    "poor quality not as described",
    "bad quality waste of money",
    "very unhappy with purchase",
    "not recommended poor quality",
    "terrible product do not buy",
    "cheap quality very disappointed",
    "bad product slow delivery",
    "poor quality not worth price",
    "very bad quality disappointed",
    "waste of money poor product",
    "not as described bad quality",
    "terrible quality not recommended",
    "poor product very unhappy",
    "bad quality broke after use",
    "very disappointed poor quality",
    "not worth buying bad product",
    "terrible purchase poor quality",
    "bad quality slow delivery",
    "very poor product disappointed",
    "not recommended waste of money",
    "poor quality bad product",
    "terrible quality very disappointed",
    "bad purchase poor quality",
    "very unhappy not recommended",
    "not as advertised poor quality",
    "waste of money bad product",
    "terrible product poor quality",
    "bad quality not worth it",
    "very disappointed bad product",
    "poor quality not recommended",
    "terrible quality waste of money",
    "bad product very unhappy",
    "not worth price poor quality",
    "very bad purchase disappointed",
    "poor product not as described",
    "terrible quality bad product",
    "bad quality very disappointed",
    "not recommended poor product",
    "waste of money terrible quality",
    "very poor quality bad product",
    "disappointed with purchase poor",
    "bad quality not worth buying",
    "terrible product very unhappy",
    "poor quality waste of money",
    "not as described very disappointed",
    "bad product poor quality",
    "very disappointed not recommended",
    "terrible quality poor product",
    "bad purchase waste of money",
    "poor quality very unhappy",
    "not worth it terrible quality",
    "bad product not recommended",
    "very poor quality disappointed",
    "terrible purchase bad quality",
    "poor product waste of money",
    "bad quality very unhappy",
    "not recommended terrible product",
    "waste of money poor quality",
    "very disappointed bad quality",
    "poor quality terrible product",
    "bad product not worth price",
    "terrible quality very unhappy",
    "not as described poor quality",
    "bad purchase very disappointed",
    "poor quality not worth it",
    "terrible product bad quality",
    "very unhappy waste of money",
    "not recommended bad product",
    "poor quality very disappointed",
    "terrible quality not worth buying",
    "bad product poor packaging",
    "very poor quality not worth it",
    "disappointed bad quality product",
    "terrible purchase not recommended",
    "poor quality bad purchase",
    "waste of money very unhappy",
    "bad quality terrible product",
]

# ── Prepare Data ──────────────────────────────────────────────────────────────
print("Preparing dataset...")
documents = POSITIVE_REVIEWS + NEGATIVE_REVIEWS
labels    = [1] * len(POSITIVE_REVIEWS) + [0] * len(NEGATIVE_REVIEWS)
print(f"Total reviews: {len(documents)} ({len(POSITIVE_REVIEWS)} positive, {len(NEGATIVE_REVIEWS)} negative)")

# ── Train/Test Split ──────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    documents, labels, test_size=0.2, random_state=42
)

# ── Vectorize ─────────────────────────────────────────────────────────────────
print("Vectorizing text...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec  = vectorizer.transform(X_test)

# ── Train ─────────────────────────────────────────────────────────────────────
print("Training Logistic Regression model...")
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred   = model.predict(X_test_vec)
accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅ Model Accuracy: {accuracy * 100:.2f}%")
print(classification_report(y_test, y_pred, target_names=["Negative", "Positive"]))

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs("model", exist_ok=True)
joblib.dump(model,      "model/sentiment_model.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")
print("✅ Model saved to model/sentiment_model.pkl")
print("✅ Vectorizer saved to model/vectorizer.pkl")
print("\nNow run: streamlit run app.py")
