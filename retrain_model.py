#!/usr/bin/env python
"""
Retrain the diabetes prediction model with the full dataset
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import os

print("=" * 70)
print("RETRAINING DIABETES PREDICTION MODEL")
print("=" * 70)

# Load dataset
csv_file = '../diabetes_prediction_india.csv'
print(f"\nLoading dataset: {csv_file}")
df = pd.read_csv(csv_file)
print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Map Diabetes_Status to binary output
df['Outcome'] = (df['Diabetes_Status'] == 'Yes').astype(int)
print(f"\nOutcome distribution:")
print(df['Outcome'].value_counts())
print(f"Diabetic (1): {(df['Outcome'] == 1).sum()} ({(df['Outcome'] == 1).sum() / len(df) * 100:.1f}%)")
print(f"Non-Diabetic (0): {(df['Outcome'] == 0).sum()} ({(df['Outcome'] == 0).sum() / len(df) * 100:.1f}%)")

# Select 8 standard features for the model
feature_cols = ['Pregnancies', 'Glucose_Tolerance_Test_Result', 'Fasting_Blood_Sugar',
                'Postprandial_Blood_Sugar', 'C_Protein_Level', 'BMI', 'Thyroid_Condition', 'Age']

X = df[feature_cols].copy().fillna(0)

# Encode categorical features
for col in X.columns:
    if X[col].dtype == 'object':
        # Try to convert to numeric, mapping Yes/No to 1/0
        X[col] = pd.to_numeric(X[col], errors='coerce')
        # Map Yes/No strings if still object type
        if X[col].dtype == 'object':
            X[col] = X[col].str.lower().map({'yes': 1, 'no': 0})
        X[col] = X[col].fillna(0)

# Convert all to float
X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
y = df['Outcome']

print(f"\nFeatures selected: {feature_cols}")
print(f"X shape: {X.shape}, y shape: {y.shape}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"\nTrain set: {X_train.shape[0]}, Test set: {X_test.shape[0]}")
print(f"Train - Diabetic: {(y_train == 1).sum()}, Non-Diabetic: {(y_train == 0).sum()}")
print(f"Test - Diabetic: {(y_test == 1).sum()}, Non-Diabetic: {(y_test == 0).sum()}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train models
print("\n" + "=" * 70)
print("TRAINING MODELS")
print("=" * 70)

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}

best_model = None
best_model_name = None
best_score = -1

for model_name, model_obj in models.items():
    print(f"\nTraining {model_name}...")
    model_obj.fit(X_train_scaled, y_train)
    
    # Evaluate on test set
    y_pred = model_obj.predict(X_test_scaled)
    test_score = model_obj.score(X_test_scaled, y_test)
    
    # Cross-validation
    cv_scores = cross_val_score(model_obj, X_train_scaled, y_train, cv=5)
    
    print(f"  Test Accuracy: {test_score:.4f}")
    print(f"  CV Score (mean): {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    print(f"  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Non-Diabetic', 'Diabetic']))
    
    if cv_scores.mean() > best_score:
        best_score = cv_scores.mean()
        best_model = model_obj
        best_model_name = model_name

print("\n" + "=" * 70)
print(f"BEST MODEL: {best_model_name} (CV Score: {best_score:.4f})")
print("=" * 70)

# Save model and scaler
os.makedirs('models', exist_ok=True)
joblib.dump(best_model, './best_model.pkl')
joblib.dump(scaler, './scaler.pkl')
print("\n✓ Models saved:")
print(f"  - ./best_model.pkl")
print(f"  - ./scaler.pkl")

# Test predictions
print("\n" + "=" * 70)
print("TEST PREDICTIONS")
print("=" * 70)

# Test with a diabetic sample from dataset
diabetic_sample = X_test[y_test == 1].iloc[0:1]
non_diabetic_sample = X_test[y_test == 0].iloc[0:1]

diabetic_scaled = scaler.transform(diabetic_sample)
non_diabetic_scaled = scaler.transform(non_diabetic_sample)

diabetic_pred = best_model.predict(diabetic_scaled)[0]
diabetic_prob = best_model.predict_proba(diabetic_scaled)[0][1]

non_diabetic_pred = best_model.predict(non_diabetic_scaled)[0]
non_diabetic_prob = best_model.predict_proba(non_diabetic_scaled)[0][1]

print(f"\nSample Diabetic case:")
print(f"  Features: {diabetic_sample.values[0]}")
print(f"  Prediction: {diabetic_pred} (Diabetic={diabetic_pred})")
print(f"  Probability: {diabetic_prob:.4f}")

print(f"\nSample Non-Diabetic case:")
print(f"  Features: {non_diabetic_sample.values[0]}")
print(f"  Prediction: {non_diabetic_pred} (Diabetic={non_diabetic_pred})")
print(f"  Probability: {non_diabetic_prob:.4f}")

print("\n" + "=" * 70)
print("RETRAINING COMPLETE")
print("=" * 70)
