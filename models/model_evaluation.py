"""
Model Evaluation Module
Comprehensive evaluation metrics and analysis
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, roc_curve, auc,
    classification_report, roc_auc_score
)
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

class ModelEvaluator:
    """
    Evaluates model performance using various metrics and visualizations
    """
    
    def __init__(self):
        """Initialize the evaluator"""
        self.results = {}
        self.models_performance = {}
        
    def evaluate_model(self, model, X_test, y_test, model_name="Model"):
        """
        Comprehensive model evaluation
        
        Args:
            model: Trained model
            X_test (np.ndarray): Test features
            y_test (np.ndarray): Test target
            model_name (str): Name of the model
            
        Returns:
            dict: Evaluation metrics
        """
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        metrics = {
            'Model': model_name,
            'Accuracy': accuracy_score(y_test, y_pred),
            'Precision': precision_score(y_test, y_pred, zero_division=0),
            'Recall': recall_score(y_test, y_pred, zero_division=0),
            'F1-Score': f1_score(y_test, y_pred, zero_division=0),
        }
        
        # Add ROC-AUC if probability predictions available
        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            metrics['ROC-AUC'] = roc_auc_score(y_test, y_pred_proba)
        except:
            metrics['ROC-AUC'] = None
        
        self.models_performance[model_name] = metrics
        
        return metrics
    
    def evaluate_multiple_models(self, models_dict, X_test, y_test):
        """
        Evaluate multiple models and compare their performance
        
        Args:
            models_dict (dict): Dictionary of models {name: model}
            X_test (np.ndarray): Test features
            y_test (np.ndarray): Test target
            
        Returns:
            pd.DataFrame: Comparison dataframe
        """
        print("\n" + "=" * 80)
        print("Model Performance Evaluation on Test Set")
        print("=" * 80)
        
        results = []
        
        for model_name, model in models_dict.items():
            metrics = self.evaluate_model(model, X_test, y_test, model_name)
            results.append(metrics)
            
            print(f"\n{model_name}:")
            print(f"  Accuracy:  {metrics['Accuracy']:.4f}")
            print(f"  Precision: {metrics['Precision']:.4f}")
            print(f"  Recall:    {metrics['Recall']:.4f}")
            print(f"  F1-Score:  {metrics['F1-Score']:.4f}")
            if metrics['ROC-AUC']:
                print(f"  ROC-AUC:   {metrics['ROC-AUC']:.4f}")
        
        results_df = pd.DataFrame(results)
        print("\n" + "=" * 80)
        print(results_df.to_string(index=False))
        print("=" * 80)
        
        return results_df
    
    def print_classification_report(self, model, X_test, y_test, model_name="Model"):
        """
        Print detailed classification report
        
        Args:
            model: Trained model
            X_test (np.ndarray): Test features
            y_test (np.ndarray): Test target
            model_name (str): Name of the model
        """
        y_pred = model.predict(X_test)
        
        print(f"\n{'=' * 60}")
        print(f"Classification Report - {model_name}")
        print(f"{'=' * 60}")
        print(classification_report(y_test, y_pred, 
                                   target_names=['Non-Diabetic', 'Diabetic']))
    
    def plot_confusion_matrix(self, model, X_test, y_test, model_name="Model", save_path=None):
        """
        Plot confusion matrix
        
        Args:
            model: Trained model
            X_test (np.ndarray): Test features
            y_test (np.ndarray): Test target
            model_name (str): Name of the model
            save_path (str): Path to save the figure
        """
        y_pred = model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Non-Diabetic', 'Diabetic'],
                   yticklabels=['Non-Diabetic', 'Diabetic'])
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"Confusion matrix saved to {save_path}")
        
        plt.show()
    
    def plot_roc_curve(self, model, X_test, y_test, model_name="Model", save_path=None):
        """
        Plot ROC curve
        
        Args:
            model: Trained model
            X_test (np.ndarray): Test features
            y_test (np.ndarray): Test target
            model_name (str): Name of the model
            save_path (str): Path to save the figure
        """
        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
            roc_auc = auc(fpr, tpr)
            
            plt.figure(figsize=(8, 6))
            plt.plot(fpr, tpr, color='darkorange', lw=2, 
                    label=f'ROC curve (AUC = {roc_auc:.2f})')
            plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title(f'ROC Curve - {model_name}')
            plt.legend(loc="lower right")
            
            if save_path:
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                print(f"ROC curve saved to {save_path}")
            
            plt.show()
        except Exception as e:
            print(f"Cannot plot ROC curve for {model_name}: {str(e)}")
    
    def plot_feature_importance(self, model, feature_names, model_name="Model", save_path=None):
        """
        Plot feature importance (for tree-based models)
        
        Args:
            model: Trained model
            feature_names (list): List of feature names
            model_name (str): Name of the model
            save_path (str): Path to save the figure
        """
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                
                indices = np.argsort(importance)[::-1]
                
                plt.figure(figsize=(10, 6))
                plt.title(f'Feature Importance - {model_name}')
                plt.bar(range(len(importance)), importance[indices])
                plt.xticks(range(len(importance)), 
                          [feature_names[i] for i in indices], rotation=45, ha='right')
                plt.ylabel('Importance')
                
                if save_path:
                    plt.savefig(save_path, dpi=100, bbox_inches='tight')
                    print(f"Feature importance plot saved to {save_path}")
                
                plt.show()
                
                # Print feature importance values
                print(f"\nFeature Importance - {model_name}:")
                for i in indices:
                    print(f"  {feature_names[i]:25} : {importance[i]:.4f}")
            else:
                print(f"Model {model_name} does not have feature importance")
        except Exception as e:
            print(f"Cannot plot feature importance: {str(e)}")
    
    def summary_report(self, best_model, best_model_name, X_test, y_test, feature_names):
        """
        Generate a comprehensive summary report
        
        Args:
            best_model: Best trained model
            best_model_name (str): Name of best model
            X_test (np.ndarray): Test features
            y_test (np.ndarray): Test target
            feature_names (list): List of feature names
        """
        print("\n" + "=" * 80)
        print("COMPREHENSIVE MODEL EVALUATION SUMMARY")
        print("=" * 80)
        
        # Performance metrics
        print(f"\nBest Model: {best_model_name}")
        self.evaluate_model(best_model, X_test, y_test, best_model_name)
        print(self.models_performance[best_model_name])
        
        # Classification report
        self.print_classification_report(best_model, X_test, y_test, best_model_name)
        
        # Feature importance
        if hasattr(best_model, 'feature_importances_'):
            print(f"\nTop 5 Important Features:")
            importance = best_model.feature_importances_
            indices = np.argsort(importance)[::-1][:5]
            for rank, i in enumerate(indices, 1):
                print(f"  {rank}. {feature_names[i]:25} : {importance[i]:.4f}")
        
        print("\n" + "=" * 80)
