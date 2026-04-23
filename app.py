from flask import Flask, render_template, request, jsonify, session
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle, os, json
from datetime import datetime
app = Flask(__name__)
app.secret_key = "sleepsense_secret_2024"
# ── Global model objects
models     = {}
scaler     = StandardScaler()
le_quality = LabelEncoder()
MODEL_PATH = "model/trained_models.pkl"
# ── Generate synthetic training dataset 
def generate_dataset(n=2000):
    np.random.seed(42)
    data = {
        "sleep_duration":   np.clip(np.random.normal(7, 1.5, n), 3, 12),
        "exercise_minutes": np.clip(np.random.normal(35, 25, n), 0, 180),
        "screen_time":      np.clip(np.random.normal(60, 40, n), 0, 240),
        "stress_level":     np.random.randint(0, 11, n),
        "caffeine":         np.random.choice([0, 1, 2, 3], n),  # none/low/mod/high
        "mood":             np.random.choice([0, 1, 2, 3], n),  # happy/neutral/anxious/sad
        "interruptions":    np.random.choice([0, 1], n),
        "bedtime_hour":     np.clip(np.random.normal(23, 1.5, n), 20, 4),
    }
    df = pd.DataFrame(data)
    # Rule-based label generation (mirrors frontend scoring)
    def label_row(r):
        score = 50
        # Duration
        if 7 <= r.sleep_duration <= 9:       score += 30
        elif 6 <= r.sleep_duration < 7:      score += 15
        elif r.sleep_duration >= 5:          score += 5
        else:                                score -= 10
        score -= r.stress_level * 2
        score -= r.screen_time * 0.1
        score += min(r.exercise_minutes / 60 * 20, 20)
        score -= r.caffeine * 8
        mood_pen = [0, -5, -18, -12]
        score += mood_pen[int(r.mood)]
        if r.interruptions == 1: 
            score -= 12
        # Classify
        if score >= 55:   return "Good"
        elif score >= 30: return "Average"
        else:             return "Poor"
    df["quality"] = df.apply(label_row, axis=1)
    return df
def train_models():
    """Train all 4 ML models and save to disk."""
    global models, scaler, le_quality
    df = generate_dataset()
    features = ["sleep_duration","exercise_minutes","screen_time",
                "stress_level","caffeine","mood","interruptions","bedtime_hour"]
    X = df[features].values
    y = le_quality.fit_transform(df["quality"])   # Good=0, Average=1, Poor=2
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)
    classifiers = {
        "Random Forest":     RandomForestClassifier(n_estimators=150, random_state=42),
        "Decision Tree":     DecisionTreeClassifier(max_depth=8, random_state=42),
        "Logistic Regression": LogisticRegression(max_iter=500, random_state=42),
        "SVM":               SVC(kernel="rbf", probability=True, random_state=42),
    }
    results = {}
    for name, clf in classifiers.items():
        Xtr = X_train_sc if name in ("Logistic Regression", "SVM") else X_train
        Xte = X_test_sc  if name in ("Logistic Regression", "SVM") else X_test
        clf.fit(Xtr, y_train)
        acc = accuracy_score(y_test, clf.predict(Xte))
        models[name] = clf
        results[name] = round(acc * 100, 2)
        print(f"  {name}: {acc*100:.1f}%")
    # Save
    os.makedirs("model", exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"models": models, "scaler": scaler, "le": le_quality}, f)
    print("✅ Models saved.")
    return results
def load_models():
    global models, scaler, le_quality
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            obj = pickle.load(f)
        models     = obj["models"]
        scaler     = obj["scaler"]
        le_quality = obj["le"]
        print("✅ Models loaded from disk.")
    else:
        print("🔧 Training models for the first time …")
        train_models()
def encode_input(data):
    """Convert form data to numeric feature vector."""
    caffeine_map = {"none": 0, "low": 1, "moderate": 2, "high": 3}
    mood_map     = {"happy": 0, "neutral": 1, "anxious": 2, "sad": 3}

    bedtime = data.get("bedtime", "23:00")
    try:
        bh = int(bedtime.split(":")[0])
    except Exception:
        bh = 23
    return np.array([[
        float(data.get("sleep_duration", 7)),
        float(data.get("exercise_minutes", 30)),
        float(data.get("screen_time", 45)),
        float(data.get("stress_level", 5)),
        caffeine_map.get(data.get("caffeine", "low"), 1),
        mood_map.get(data.get("mood", "neutral"), 1),
        1 if data.get("interruptions") == "yes" else 0,
        bh,
    ]])
def get_tips(data, quality):
    """Generate personalised tips based on input."""
    tips = []
    dur    = float(data.get("sleep_duration", 7))
    stress = int(data.get("stress_level", 5))
    screen = float(data.get("screen_time", 45))
    ex     = float(data.get("exercise_minutes", 30))
    caf    = data.get("caffeine", "low")
    mood   = data.get("mood", "neutral")
    intr   = data.get("interruptions", "no")
    if dur < 7:
        tips.append({"icon": "🛏️", "text": f"Aim for 7–9 hours. You slept {dur}h — try going to bed 30 minutes earlier."})
    if dur > 9.5:
        tips.append({"icon": "⏰", "text": "Oversleeping disrupts circadian rhythms. A consistent wake-up time helps most."})
    if stress >= 7:
        tips.append({"icon": "🧘", "text": "High stress detected. Try 10 min of box-breathing or guided meditation before bed."})
    if screen > 60:
        tips.append({"icon": "📵", "text": f"Cut screen time by at least {int(screen*0.4)} min. Blue light delays melatonin by up to 3 hours."})
    if ex < 20:
        tips.append({"icon": "🏃", "text": "Even a 20-min brisk walk improves slow-wave sleep by up to 15%."})
    if caf in ("moderate", "high"):
        tips.append({"icon": "☕", "text": "Avoid caffeine after 2 PM — it has a 5–7 hour half-life that disrupts deep sleep."})
    if mood == "anxious":
        tips.append({"icon": "🌬️", "text": "Try the 4-7-8 technique: inhale 4s, hold 7s, exhale 8s to activate the parasympathetic system."})
    if mood == "sad":
        tips.append({"icon": "💜", "text": "A warm bath 1–2 hours before bed lowers core body temp, signalling sleep to the brain."})
    if intr == "yes":
        tips.append({"icon": "🔇", "text": "Sleep interruptions fragment REM. Try white noise, earplugs, or a cooler room (18–20 °C)."})
    if quality == "Good":
        tips.append({"icon": "✅", "text": "Excellent habits! Keep your routine stable — consistency is the #1 predictor of sleep quality."})
        tips.append({"icon": "🌿", "text": "Consider magnesium glycinate (200–400 mg) before bed to deepen sleep stages."})
    if not tips:
        tips.append({"icon": "💤", "text": "Your sleep profile looks balanced. Track for a week to spot subtle patterns."})
    return tips[:6]
# ── Routes 
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    algo = data.get("algorithm", "Random Forest")
    if algo not in models:
        return jsonify({"error": f"Model '{algo}' not found."}), 400

    X = encode_input(data)
    clf = models[algo]
    # Scale if needed
    if algo in ("Logistic Regression", "SVM"):
        X_in = scaler.transform(X)
    else:
        X_in = X
    pred       = clf.predict(X_in)[0]
    proba      = clf.predict_proba(X_in)[0]
    quality    = le_quality.inverse_transform([pred])[0]
    confidence = round(float(max(proba)) * 100, 1)
    # Score (0–100)
    class_scores = {"Good": 85, "Average": 55, "Poor": 25}
    base = class_scores[quality]
    score = int(base + (confidence - 70) * 0.3)
    score = max(10, min(99, score))
    tips = get_tips(data, quality)
    # Factor importances (Random Forest only, else uniform)
    feature_names = ["Sleep Duration","Exercise","Screen Time",
                     "Stress Level","Caffeine","Mood","Interruptions","Bedtime"]
    if hasattr(clf, "feature_importances_"):
        fi = clf.feature_importances_
        importances = {n: round(float(v)*100, 1) for n, v in zip(feature_names, fi)}
    else:
        importances = {n: round(100/len(feature_names), 1) for n in feature_names}
    # Save to session history
    if "history" not in session:
        session["history"] = []
    entry = {
        "date":       datetime.now().strftime("%d %b %Y"),
        "time":       datetime.now().strftime("%H:%M"),
        "quality":    quality,
        "score":      score,
        "confidence": confidence,
        "algorithm":  algo,
    }
    session["history"] = ([entry] + session["history"])[:10]
    session.modified = True

    return jsonify({
        "quality":     quality,
        "score":       score,
        "confidence":  confidence,
        "algorithm":   algo,
        "tips":        tips,
        "importances": importances,
        "proba": {
            le_quality.inverse_transform([i])[0]: round(float(p)*100,1)
            for i, p in enumerate(proba)
        }
    })
@app.route("/history")
def get_history():
    return jsonify(session.get("history", []))
@app.route("/model-accuracy")
def model_accuracy():
    """Return pre-computed accuracies (re-train if needed)."""
    acc_path = "model/accuracies.json"
    if os.path.exists(acc_path):
        with open(acc_path) as f:
            return jsonify(json.load(f))
    # Compute on-the-fly
    df = generate_dataset()
    features = ["sleep_duration","exercise_minutes","screen_time",
                "stress_level","caffeine","mood","interruptions","bedtime_hour"]
    X = df[features].values
    y = le_quality.transform(df["quality"])
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    acc = {}
    for name, clf in models.items():
        Xi = scaler.transform(X_test) if name in ("Logistic Regression","SVM") else X_test
        acc[name] = round(accuracy_score(y_test, clf.predict(Xi)) * 100, 2)
    with open(acc_path, "w") as f:
        json.dump(acc, f)
    return jsonify(acc)
if __name__ == "__main__":
    load_models()
    app.run(debug=True, port=5000)
