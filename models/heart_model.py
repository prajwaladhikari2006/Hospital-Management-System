import numpy as np
import pandas as pd
import pickle, os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

MODEL_PATH  = "heart_model.pkl"
SCALER_PATH = "heart_scaler.pkl"
FEATURES    = ["age","sex","cp","trestbps","chol","fbs",
               "restecg","thalach","exang","oldpeak","slope","ca","thal"]

def generate_sample_data(n=500):
    np.random.seed(42)
    h = n // 2
    healthy = pd.DataFrame({
        "age": np.random.randint(30, 65, h),
        "sex": np.random.randint(0, 2, h),
        "cp":  np.random.choice([0,1], h, p=[0.7,0.3]),
        "trestbps": np.random.randint(100, 130, h),
        "chol":     np.random.randint(150, 230, h),
        "fbs":      np.random.choice([0,1], h, p=[0.85,0.15]),
        "restecg":  np.random.choice([0,1,2], h, p=[0.5,0.4,0.1]),
        "thalach":  np.random.randint(140, 200, h),
        "exang":    np.random.choice([0,1], h, p=[0.8,0.2]),
        "oldpeak":  np.round(np.random.uniform(0.0, 1.5, h), 1),
        "slope":    np.random.choice([0,1,2], h, p=[0.1,0.6,0.3]),
        "ca":       np.random.choice([0,1,2,3], h, p=[0.6,0.25,0.1,0.05]),
        "thal":     np.random.choice([1,2,3], h, p=[0.5,0.3,0.2]),
        "target":   np.zeros(h, dtype=int)
    })
    r = n - h
    risky = pd.DataFrame({
        "age": np.random.randint(50, 80, r),
        "sex": np.random.choice([0,1], r, p=[0.35,0.65]),
        "cp":  np.random.choice([0,1,2,3], r, p=[0.1,0.2,0.3,0.4]),
        "trestbps": np.random.randint(130, 180, r),
        "chol":     np.random.randint(220, 350, r),
        "fbs":      np.random.choice([0,1], r, p=[0.6,0.4]),
        "restecg":  np.random.choice([0,1,2], r, p=[0.2,0.3,0.5]),
        "thalach":  np.random.randint(90, 150, r),
        "exang":    np.random.choice([0,1], r, p=[0.3,0.7]),
        "oldpeak":  np.round(np.random.uniform(1.5, 5.0, r), 1),
        "slope":    np.random.choice([0,1,2], r, p=[0.4,0.4,0.2]),
        "ca":       np.random.choice([0,1,2,3], r, p=[0.2,0.3,0.3,0.2]),
        "thal":     np.random.choice([1,2,3], r, p=[0.1,0.3,0.6]),
        "target":   np.ones(r, dtype=int)
    })
    df = pd.concat([healthy, risky], ignore_index=True)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)

def train_model():
    df = generate_sample_data(500)
    X, y = df[FEATURES], df["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train_s, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_s))
    print(f"Accuracy: {acc*100:.2f}%")

    with open(MODEL_PATH, "wb")  as f: pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f: pickle.dump(scaler, f)
    return model, scaler

def load_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        train_model()
    with open(MODEL_PATH, "rb")  as f: model  = pickle.load(f)
    with open(SCALER_PATH, "rb") as f: scaler = pickle.load(f)
    return model, scaler

def predict_heart_disease(inputs):
    model, scaler = load_model()
    arr = np.array([[inputs[col] for col in FEATURES]])
    arr_scaled = scaler.transform(arr)
    pred  = model.predict(arr_scaled)[0]
    proba = model.predict_proba(arr_scaled)[0]
    confidence = round(float(proba[pred]) * 100, 2)
    label = "High Risk" if pred == 1 else "Low Risk"
    return label, confidence

if __name__ == "__main__":
    train_model()
