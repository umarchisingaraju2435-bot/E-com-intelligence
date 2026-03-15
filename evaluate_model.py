from sentiment_model import predict, predict_proba
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)
import numpy as np

# ── Labelled Test Dataset ─────────────────────────────────────────────────────
TEST_DATA = [
    # positive reviews
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
    ("best laptop i have bought",                    "positive"),

    # negative reviews
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

# ── Run Predictions ───────────────────────────────────────────────────────────
print("\n⏳ Loading BERT and running predictions...\n")

texts     = [d[0] for d in TEST_DATA]
actual    = [d[1] for d in TEST_DATA]
predicted = [predict(t) for t in texts]
probas    = [predict_proba(t) for t in texts]

# ── 1. Classification Report ──────────────────────────────────────────────────
print("=" * 55)
print("         CLASSIFICATION REPORT")
print("=" * 55)
print(classification_report(actual, predicted, target_names=["negative", "positive"]))

# ── 2. Confusion Matrix ───────────────────────────────────────────────────────
cm = confusion_matrix(actual, predicted, labels=["positive", "negative"])
TP, FN = cm[0][0], cm[0][1]
FP, TN = cm[1][0], cm[1][1]

print("=" * 55)
print("              CONFUSION MATRIX")
print("=" * 55)
print(f"                  Predicted")
print(f"                  Pos    Neg")
print(f"  Actual  Pos  [  {TP:2d}   |  {FN:2d}  ]  ← True Pos | False Neg")
print(f"          Neg  [  {FP:2d}   |  {TN:2d}  ]  ← False Pos | True Neg")
print()
print(f"  TP (correct positive) : {TP}")
print(f"  TN (correct negative) : {TN}")
print(f"  FP (wrong positive)   : {FP}")
print(f"  FN (wrong negative)   : {FN}")

# ── 3. Bias and Variance ──────────────────────────────────────────────────────
accuracy    = accuracy_score(actual, predicted)

# bias = how wrong the model is on average (error rate = 1 - accuracy)
bias        = round(1 - accuracy, 4)

# variance = how much predictions fluctuate (std dev of confidence scores)
proba_array = np.array(probas)
variance    = round(float(np.var(proba_array)), 4)
std_dev     = round(float(np.std(proba_array)), 4)

print()
print("=" * 55)
print("            BIAS AND VARIANCE")
print("=" * 55)
print(f"  Accuracy          : {round(accuracy * 100, 2)}%")
print(f"  Bias (error rate) : {bias}  → {'LOW ✅ model is accurate' if bias < 0.1 else 'HIGH ❌ model underfitting'}")
print(f"  Variance          : {variance}  → {'LOW ✅ model is stable' if variance < 0.1 else 'HIGH ❌ model overfitting'}")
print(f"  Std Deviation     : {std_dev}")
print()

if bias < 0.1 and variance < 0.1:
    print("  ✅ LOW BIAS + LOW VARIANCE → Model is well fitted")
elif bias < 0.1 and variance >= 0.1:
    print("  ⚠️  LOW BIAS + HIGH VARIANCE → Model is overfitting")
elif bias >= 0.1 and variance < 0.1:
    print("  ⚠️  HIGH BIAS + LOW VARIANCE → Model is underfitting")
else:
    print("  ❌ HIGH BIAS + HIGH VARIANCE → Model needs improvement")

# ── 4. Per Review Breakdown ───────────────────────────────────────────────────
print()
print("=" * 55)
print("           PER REVIEW BREAKDOWN")
print("=" * 55)
print(f"  {'Review':<45} {'Actual':<10} {'Predicted':<10} {'Conf'}")
print("-" * 55)
for text, act, pred, prob in zip(texts, actual, predicted, probas):
    match = "✅" if act == pred else "❌"
    print(f"  {match} {text[:42]:<42} {act:<10} {pred:<10} {prob}")
print("=" * 55)
