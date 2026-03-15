"""
Compare performance of:
  Model 1 — TF-IDF + Logistic Regression
  Model 2 — BERT Embeddings + Logistic Regression (retrained)
  Model 3 — BERT nlptown (standalone classifier, reference)
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from transformers import AutoTokenizer, AutoModel
import torch
from train_model import POSITIVE_REVIEWS, NEGATIVE_REVIEWS

# ── Shared Test Dataset ───────────────────────────────────────────────────────
TEST_DATA = [
    ("excellent product, highly recommended",        "positive"),
    ("amazing quality, best purchase ever",          "positive"),
    ("superb quality, fast delivery",                "positive"),
    ("good build quality, satisfied",                "positive"),
    ("value for money, fast delivery",               "positive"),
    ("great product, very satisfied",                "positive"),
    ("outstanding product, exceeded expectations",   "positive"),
    ("perfect product, love it",                     "positive"),
    ("fast delivery, good packaging",                "positive"),
    ("recommended, works as expected",               "positive"),
    ("brilliant quality, great packaging",           "positive"),
    ("top quality, very satisfied",                  "positive"),
    ("fantastic product, will buy again",            "positive"),
    ("good quality product, happy with purchase",    "positive"),
    ("best product i have bought",                   "positive"),
    ("waste of money, not recommended",              "negative"),
    ("terrible product, completely useless",         "negative"),
    ("bad quality, very disappointed",               "negative"),
    ("poor packaging, arrived damaged",              "negative"),
    ("slow delivery, disappointing",                 "negative"),
    ("below average quality, not worth it",          "negative"),
    ("not great quality for the price",              "negative"),
    ("average at best, many issues",                 "negative"),
    ("very poor quality, broke after one day",       "negative"),
    ("poor build quality, not recommended",          "negative"),
    ("not satisfied, expected better quality",       "negative"),
    ("cheap material, broke immediately",            "negative"),
    ("do not buy, complete waste",                   "negative"),
    ("terrible experience, avoid this product",      "negative"),
    ("bad product, money wasted",                    "negative"),
]

texts  = [d[0] for d in TEST_DATA]
actual = [d[1] for d in TEST_DATA]

# ── BERT Embedding Extractor ──────────────────────────────────────────────────
print("\n⏳ Loading BERT tokenizer and model for embedding extraction...")
tokenizer  = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
bert_model = AutoModel.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
bert_model.eval()
print("✅ BERT loaded.\n")

def get_bert_embeddings(text_list):
    """Extract [CLS] token embeddings from BERT for a list of texts."""
    embeddings = []
    with torch.no_grad():
        for text in text_list:
            inputs = tokenizer(text, return_tensors="pt", truncation=True,
                               max_length=128, padding=True)
            outputs = bert_model(**inputs)
            # CLS token = first token of last hidden state
            cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
            embeddings.append(cls_embedding)
    return np.array(embeddings)

def print_results(name, actual, predicted, probas):
    accuracy = accuracy_score(actual, predicted)
    bias     = round(1 - accuracy, 4)
    variance = round(float(np.var(np.array(probas))), 4)

    print(f"\nAccuracy  : {round(accuracy * 100, 2)}%")
    print(f"Bias      : {bias}  ({'LOW ✅' if bias < 0.1 else 'HIGH ❌'})")
    print(f"Variance  : {variance}  ({'LOW ✅' if variance < 0.1 else 'HIGH ❌'})")
    print("\n--- Classification Report ---")
    print(classification_report(actual, predicted, target_names=["negative", "positive"]))

    cm = confusion_matrix(actual, predicted, labels=["positive", "negative"])
    TP, FN = int(cm[0][0]), int(cm[0][1])
    FP, TN = int(cm[1][0]), int(cm[1][1])
    print("--- Confusion Matrix ---")
    print(f"                  Predicted")
    print(f"                  Pos    Neg")
    print(f"  Actual  Pos  [  {TP:2d}   |  {FN:2d}  ]")
    print(f"          Neg  [  {FP:2d}   |  {TN:2d}  ]")
    print(f"\n  TP={TP}  TN={TN}  FP={FP}  FN={FN}")
    return accuracy, bias, variance

# ── Model 1: TF-IDF + Logistic Regression ────────────────────────────────────
print("=" * 60)
print("  MODEL 1 — TF-IDF + Logistic Regression")
print("=" * 60)

train_docs   = POSITIVE_REVIEWS + NEGATIVE_REVIEWS
train_labels = ["positive"] * len(POSITIVE_REVIEWS) + ["negative"] * len(NEGATIVE_REVIEWS)

tfidf      = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train_tf = tfidf.fit_transform(train_docs)
lr_tfidf   = LogisticRegression(max_iter=1000)
lr_tfidf.fit(X_train_tf, train_labels)

X_test_tf    = tfidf.transform(texts)
tfidf_pred   = lr_tfidf.predict(X_test_tf)
tfidf_probas = lr_tfidf.predict_proba(X_test_tf).max(axis=1)

m1_acc, m1_bias, m1_var = print_results("TF-IDF + LR", actual, tfidf_pred, tfidf_probas)

# ── Model 2: BERT Embeddings + Logistic Regression ───────────────────────────
print("\n" + "=" * 60)
print("  MODEL 2 — BERT Embeddings + Logistic Regression")
print("=" * 60)
print("\n⏳ Extracting BERT embeddings for 200 training reviews...")

X_train_bert = get_bert_embeddings(train_docs)
lr_bert      = LogisticRegression(max_iter=1000)
lr_bert.fit(X_train_bert, train_labels)
print("✅ LR retrained on BERT embeddings.")

print("⏳ Extracting BERT embeddings for 30 test reviews...")
X_test_bert   = get_bert_embeddings(texts)
bert_lr_pred  = lr_bert.predict(X_test_bert)
bert_lr_proba = lr_bert.predict_proba(X_test_bert).max(axis=1)

m2_acc, m2_bias, m2_var = print_results("BERT + LR", actual, bert_lr_pred, bert_lr_proba)

# ── Model 3: BERT nlptown standalone (reference) ─────────────────────────────
print("\n" + "=" * 60)
print("  MODEL 3 — BERT nlptown (standalone classifier, reference)")
print("=" * 60)
print("\n⏳ Running nlptown BERT predictions...")

from sentiment_model import predict as bert_predict, predict_proba as bert_proba
bert_pred   = [bert_predict(t) for t in texts]
bert_probas = [bert_proba(t) for t in texts]

m3_acc, m3_bias, m3_var = print_results("BERT nlptown", actual, bert_pred, bert_probas)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  COMPARISON SUMMARY")
print("=" * 60)
print(f"  {'Metric':<20} {'TF-IDF + LR':<20} {'BERT + LR':<20} {'BERT nlptown':<20}")
print(f"  {'-'*78}")
print(f"  {'Accuracy':<20} {str(round(m1_acc*100,2))+'%':<20} {str(round(m2_acc*100,2))+'%':<20} {str(round(m3_acc*100,2))+'%':<20}")
print(f"  {'Bias':<20} {str(m1_bias):<20} {str(m2_bias):<20} {str(m3_bias):<20}")
print(f"  {'Variance':<20} {str(m1_var):<20} {str(m2_var):<20} {str(m3_var):<20}")

best_acc = max(m1_acc, m2_acc, m3_acc)
print(f"  {'Winner':<20} {'✅' if m1_acc == best_acc else '❌':<20} {'✅' if m2_acc == best_acc else '❌':<20} {'✅' if m3_acc == best_acc else '❌':<20}")
print("=" * 60)
