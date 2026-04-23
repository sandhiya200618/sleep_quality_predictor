# 🌙 SleepSense — Sleep Quality Predictor

A full-stack ML web app that predicts sleep quality (Good / Average / Poor)
from lifestyle and health inputs, built with Flask + scikit-learn.

---

## 📁 Project Structure

```
sleep_predictor/
├── app.py                  ← Flask backend + ML training + API routes
├── requirements.txt        ← Python dependencies
├── model/
│   └── trained_models.pkl  ← Auto-generated on first run
├── templates/
│   └── index.html          ← Jinja2 HTML template
└── static/
    ├── css/
    │   └── style.css       ← Nighttime UI styles
    └── js/
        └── app.js          ← Frontend logic (fetch, render, interactions)
```

---

## 🚀 Setup & Run

### 1. Clone / download the project
```bash
cd sleep_predictor
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

### 5. Open in browser
```
http://localhost:5000
```

The first run automatically trains all 4 ML models and saves them to `model/`.

---

## 🤖 ML Algorithms Used

| Algorithm           | Notes                                 |
|---------------------|---------------------------------------|
| Random Forest       | Best overall accuracy (~89%)          |
| Decision Tree       | Fast, interpretable                   |
| Logistic Regression | Linear baseline (uses StandardScaler) |
| SVM (RBF kernel)    | High accuracy on scaled features      |

Switch between algorithms using the tab bar in the UI.

---

## 📥 Input Features

| Feature             | Type     | Range/Options                  |
|---------------------|----------|-------------------------------|
| Sleep Duration      | Numeric  | 0–12 hours                    |
| Bedtime             | Time     | HH:MM                         |
| Wake-up Time        | Time     | HH:MM                         |
| Exercise Duration   | Numeric  | 0–300 minutes                 |
| Screen Time         | Numeric  | 0–300 minutes before bed      |
| Stress Level        | Slider   | 0–10                          |
| Caffeine Intake     | Dropdown | None / Low / Moderate / High  |
| Mood Before Sleep   | Dropdown | Happy / Neutral / Anxious / Sad|
| Sleep Interruptions | Radio    | Yes / No                      |

---

## 📤 Output

- **Predicted Quality**: Good / Average / Poor
- **Sleep Score**: 0–100
- **Model Confidence**: %
- **Class Probabilities**: bar chart for all 3 classes
- **Feature Importance**: ranked bar chart
- **Personalised Tips**: up to 6 actionable recommendations
- **History**: last 10 predictions (session-based)
- **Model Accuracy**: comparison of all 4 algorithms

---

## 🔌 API Endpoints

| Endpoint            | Method | Description               |
|---------------------|--------|---------------------------|
| `/`                 | GET    | Main UI                   |
| `/predict`          | POST   | JSON → prediction result  |
| `/history`          | GET    | Session prediction history|
| `/model-accuracy`   | GET    | Accuracy of all 4 models  |

### POST /predict — Example payload
```json
{
  "sleep_duration": 6.5,
  "exercise_minutes": 20,
  "screen_time": 90,
  "stress_level": 7,
  "caffeine": "moderate",
  "mood": "anxious",
  "interruptions": "yes",
  "bedtime": "00:30",
  "algorithm": "Random Forest"
}
```

---

## 📊 Dataset

Training data is synthetically generated (2,000 records) using realistic
distributions and rule-based labels. You can replace this with real datasets:

- [Sleep Health and Lifestyle Dataset — Kaggle](https://www.kaggle.com/datasets/uom190346a/sleep-health-and-lifestyle-dataset)
- [Sleep Efficiency Dataset — UCI ML Repo](https://archive.ics.uci.edu/dataset/912/sleep+efficiency)

To use a real dataset, replace `generate_dataset()` in `app.py` with your
own CSV loading + preprocessing code.

---

## 🛠️ Extending the Project

- **Add a database** (SQLite/PostgreSQL) for persistent history
- **Export predictions** as CSV or PDF
- **Add charts** (matplotlib/seaborn) for trend analysis
- **Deploy** to Heroku, Render, or AWS with `gunicorn app:app`
- **Mobile app**: wrap the API with React Native or Flutter

---

## ⚠️ Disclaimer

SleepSense is for educational purposes only. It is not a medical device.
For serious sleep concerns, consult a healthcare professional.
