#!/usr/bin/env python
"""
Create a simple rule-based + threshold model for diabetic prediction
that works with the standard 8-feature schema
"""
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler

print("=" * 70)
print("CREATING RULE-BASED DIABETES PREDICTION MODEL")
print("=" * 70)

class SimpleRuleBasedDiabetesModel:
    """
    Rule-based model that predicts diabetic status using clinical thresholds
    and feature combinations
    """
    def __init__(self):
        self.classes_ = np.array([0, 1])
    
    def predict(self, X):
        """
        Predict diabetic status based on rules
        X shape: (n_samples, 8) - [pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, dpf, age]
        """
        predictions = []
        for sample in X:
            pred = self._predict_single(sample)
            predictions.append(pred)
        return np.array(predictions)
    
    def _predict_single(self, features):
        """Predict for a single sample"""
        pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, dpf, age = features
        
        # Strong diabetic indicators
        score = 0
        
        # Glucose is the strongest predictor
        if glucose >= 180:
            score += 3
        elif glucose >= 150:
            score += 2
        elif glucose >= 125:
            score += 1
        
        # BMI
        if bmi >= 35:
            score += 2
        elif bmi >= 30:
            score += 1
        
        # Age
        if age >= 50:
            score += 1
        
        # Insulin (high insulin can indicate insulin resistance)
        if insulin >= 200:
            score += 1
        
        # Diabetes pedigree function
        if dpf >= 0.8:
            score += 1
        
        # Blood pressure
        if blood_pressure >= 100:
            score += 1
        
        # Decision threshold
        if score >= 4:
            return 1  # Diabetic
        else:
            return 0   # Non-Diabetic
    
    def predict_proba(self, X):
        """
        Predict probability for both classes
        """
        predictions = self.predict(X)
        proba = np.zeros((X.shape[0], 2))
        
        for i, pred in enumerate(predictions):
            if pred == 1:
                # Diabetic prediction
                proba[i] = [0.2, 0.8]  # 20% non-diabetic, 80% diabetic
            else:
                # Non-diabetic prediction
                proba[i] = [0.75, 0.25]  # 75% non-diabetic, 25% diabetic
        
        return proba

# Create and save the model
print("\nCreating rule-based model...")
model = SimpleRuleBasedDiabetesModel()

# Create a standard scaler (even though we'll use rules)
# Generate dummy training data for scaler reference
dummy_X = np.array([
    [1, 100, 72, 23, 30, 22.5, 0.3, 25],
    [2, 160, 90, 35, 120, 32.5, 0.6, 42],
    [0, 95, 70, 20, 20, 21, 0.2, 30],
    [5, 250, 120, 45, 300, 40, 1.5, 55]
])

scaler = StandardScaler()
scaler.fit(dummy_X)

print("Model classes:", model.classes_)
print("Model created successfully")

# Test predictions
print("\n" + "=" * 70)
print("TEST PREDICTIONS")
print("=" * 70)

test_cases = [
    # Non-diabetic case
    np.array([[1, 100, 72, 23, 30, 22.5, 0.3, 25]]),
    # Mild diabetic case
    np.array([[2, 140, 85, 30, 100, 28, 0.5, 40]]),
    # Strong diabetic case
    np.array([[5, 250, 120, 45, 300, 40, 1.5, 55]]),
    # Extreme diabetic case
    np.array([[6, 280, 130, 50, 350, 42, 2.0, 60]])
]

test_labels = ["Non-Diabetic", "Mild Diabetic", "Strong Diabetic", "Extreme Diabetic"]

for i, (test_X, label) in enumerate(zip(test_cases, test_labels)):
    # Scale the features
    test_X_scaled = scaler.transform(test_X)
    
    # Make predictions
    pred = model.predict(test_X)[0]
    prob = model.predict_proba(test_X)[0]
    
    print(f"\nTest Case {i+1}: {label}")
    print(f"  Raw features: {test_X[0]}")
    print(f"  Prediction: {pred} ({'Diabetic' if pred == 1 else 'Non-Diabetic'})")
    print(f"  Probability: Non-Diabetic={prob[0]:.2%}, Diabetic={prob[1]:.2%}")

# Save the model and scaler
print("\n" + "=" * 70)
print("SAVING MODELS")
print("=" * 70)

joblib.dump(model, './best_model.pkl')
joblib.dump(scaler, './scaler.pkl')

print("✓ Models saved:")
print(f"  - ./best_model.pkl (Rule-based model)")
print(f"  - ./scaler.pkl (StandardScaler)")

print("\n" + "=" * 70)
print("MODEL CREATION COMPLETE")
print("=" * 70)
print("\nThe rule-based model uses these thresholds:")
print("  - Glucose >= 180: +3 points")
print("  - Glucose >= 150: +2 points")
print("  - Glucose >= 125: +1 point")
print("  - BMI >= 35: +2 points")
print("  - BMI >= 30: +1 point")
print("  - Age >= 50: +1 point")
print("  - Insulin >= 200: +1 point")
print("  - Diabetes Pedigree >= 0.8: +1 point")
print("  - Blood Pressure >= 100: +1 point")
print("\nDecision: Diabetic if score >= 4, otherwise Non-Diabetic")
