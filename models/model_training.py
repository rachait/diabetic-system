"""
Model Training Module
Trains multiple classification models for diabetes prediction
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import cross_val_score, GridSearchCV
import joblib
import warnings

warnings.filterwarnings('ignore')

class ModelTrainer:
    """
    Trains and evaluates multiple classification models
    """
    
    def __init__(self):
        """Initialize the model trainer"""
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.cv_scores = {}
        
    def create_models(self):
        """
        Create multiple classification models with different algorithms
        
        Returns:
            dict: Dictionary of models
        """
        models = {
            'Logistic Regression': LogisticRegression(
    random_state=42,
    max_iter=1000,
    class_weight='balanced'
),
           'Random Forest': RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight='balanced'
),
            
            'Gradient Boosting': GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    random_state=42
),
           'SVM': SVC(
    kernel='rbf',
    probability=True,
    class_weight='balanced',
    random_state=42
),
           
'XGBoost': XGBClassifier(
    scale_pos_weight=3,
    use_label_encoder=False,
    eval_metric='logloss'
),
            'KNN': KNeighborsClassifier(
                n_neighbors=5, n_jobs=-1
            ),
            'Decision Tree': DecisionTreeClassifier(
                random_state=42, max_depth=10
            ),
            'Naive Bayes': GaussianNB()
        }
        
        self.models = models
        print(f"Created {len(models)} models: {list(models.keys())}")
        return models
    
    
    def train_models(self, X_train, y_train):
        """
        Train all models
        
        Args:
            X_train (np.ndarray): Training features
            y_train (np.ndarray): Training target
        """
        print("\n" + "=" * 60)
        print("Training Models")
        print("=" * 60)
        
        for name, model in self.models.items():
            print(f"\nTraining {name}...", end=" ")
            model.fit(X_train, y_train)
            print("✓ Complete")
        
        print("\n" + "=" * 60)
        print("All models trained successfully!")
        print("=" * 60)
    
    def evaluate_with_cv(self, X_train, y_train, cv=5):
        """
        Evaluate models using cross-validation
        
        Args:
            X_train (np.ndarray): Training features
            y_train (np.ndarray): Training target
            cv (int): Number of cross-validation folds
        """
        print("\n" + "=" * 60)
        print(f"Cross-Validation Evaluation (CV={cv})")
        print("=" * 60)
        
        results = []
        
        for name, model in self.models.items():
            scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='f1')
            self.cv_scores[name] = scores
            
            mean_score = scores.mean()
            std_score = scores.std()
            
            results.append({
                'Model': name,
                'Mean Accuracy': f"{mean_score:.4f}",
                'Std Dev': f"{std_score:.4f}",
                'Min': f"{scores.min():.4f}",
                'Max': f"{scores.max():.4f}"
            })
            
            print(f"{name:20} | Accuracy: {mean_score:.4f} (+/- {std_score:.4f})")
        
        results_df = pd.DataFrame(results)
        print("\n" + results_df.to_string(index=False))
        
        return results_df
    
    def select_best_model(self):
        """
        Select the best model based on cross-validation score
        
        Returns:
            tuple: (best_model, model_name)
        """
        if not self.cv_scores:
            raise ValueError("No CV scores available. Run evaluate_with_cv() first.")
        
        # Calculate mean CV score for each model
        mean_scores = {name: scores.mean() for name, scores in self.cv_scores.items()}
        
        self.best_model_name = max(mean_scores, key=mean_scores.get)
        self.best_model = self.models[self.best_model_name]
        
        print("\n" + "=" * 60)
        print(f"Best Model Selected: {self.best_model_name}")
        print(f"Best Cross-Validation Accuracy: {mean_scores[self.best_model_name]:.4f}")
        print("=" * 60)
        
        return self.best_model, self.best_model_name
    
    def hyperparameter_tuning(self, X_train, y_train, model_name='Random Forest'):
        """
        Perform hyperparameter tuning for a specific model
        
        Args:
            X_train (np.ndarray): Training features
            y_train (np.ndarray): Training target
            model_name (str): Name of the model to tune
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        print(f"\nPerforming Hyperparameter Tuning for {model_name}...")
        
        # Define parameter grids for different models
        param_grids = {
            'Random Forest': {
                'n_estimators': [100, 200],
                'max_depth': [5, 10, 15],
                'min_samples_split': [2, 5, 10]
            },
            'Gradient Boosting': {
                'n_estimators': [100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1]
            },
            'SVM': {
                'C': [0.1, 1, 10],
                'kernel': ['linear', 'rbf']
            },
            'KNN': {
                'n_neighbors': [3, 5, 7, 9],
                'weights': ['uniform', 'distance']
            },
            

        }
        
        if model_name not in param_grids:
            print(f"No predefined parameter grid for {model_name}")
            return
        
        grid_search = GridSearchCV(
            self.models[model_name],
            param_grids[model_name],
            cv=5,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        print(f"\nBest parameters: {grid_search.best_params_}")
        print(f"Best CV Accuracy: {grid_search.best_score_:.4f}")
        
        # Update the model with best parameters
        self.models[model_name] = grid_search.best_estimator_
        
        return grid_search.best_estimator_
    
    def save_model(self, path):
        """
        Save the best model to a file
        
        Args:
            path (str): Path to save the model
        """
        if self.best_model is None:
            raise ValueError("No best model selected. Run select_best_model() first.")
        
        joblib.dump(self.best_model, path)
        print(f"Best model ({self.best_model_name}) saved to {path}")
    
    def load_model(self, path):
        """
        Load a model from a file
        
        Args:
            path (str): Path to load the model from
        """
        self.best_model = joblib.load(path)
        print(f"Model loaded from {path}")
    
    def get_model_info(self):
        """Get information about the best model"""
        if self.best_model is None:
            return None
        
        info = {
            'Model Name': self.best_model_name,
            'Model Type': type(self.best_model).__name__,
            'Parameters': self.best_model.get_params()
        }
        return info
