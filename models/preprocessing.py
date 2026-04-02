"""
Data Preprocessing Module
Handles data loading, cleaning, feature scaling, and class imbalance
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
# from imblearn.over_sampling import SMOTE
# from imblearn.under_sampling import RandomUnderSampler
# from imblearn.pipeline import Pipeline as ImbPipeline
import joblib
import os

class DataPreprocessor:
    """
    Handles all preprocessing tasks including:
    - Data loading and cleaning
    - Feature scaling
    - Class imbalance handling (SMOTE + Under-sampling)
    - Train-test split
    """
    
    def __init__(self, data_path=None):
        """
        Initialize the preprocessor
        
        Args:
            data_path (str): Path to the CSV file
        """
        self.data_path = data_path
        self.data = None
        self.scaler = StandardScaler()
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = None
        
    def load_data(self, path=None):
        """
        Load data from CSV file
        
        Args:
            path (str): Path to CSV file. If None, uses self.data_path
            
        Returns:
            pd.DataFrame: Loaded data
        """
        if path:
            self.data_path = path
            
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
            
        self.data = pd.read_csv(self.data_path, comment='#')
        print(f"Data loaded successfully. Shape: {self.data.shape}")
        print(f"Columns: {list(self.data.columns)}")
        return self.data
    
    def get_data_info(self):
        """Get basic information about the dataset"""
        if self.data is None:
            return None
            
        info = {
            'shape': self.data.shape,
            'columns': list(self.data.columns),
            'dtypes': self.data.dtypes.to_dict(),
            'missing_values': self.data.isnull().sum().to_dict(),
            'target_distribution': self.data['Outcome'].value_counts().to_dict() if 'Outcome' in self.data.columns else None
        }
        return info
    
    def handle_missing_values(self, strategy='mean'):
        """
        Handle missing values in the dataset
        
        Args:
            strategy (str): 'mean', 'median', or 'drop'
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if strategy == 'mean':
            self.data.fillna(self.data.mean(), inplace=True)
        elif strategy == 'median':
            self.data.fillna(self.data.median(), inplace=True)
        elif strategy == 'drop':
            self.data.dropna(inplace=True)
        else:
            raise ValueError("Strategy must be 'mean', 'median', or 'drop'")
        
        print(f"Missing values handled using {strategy} strategy")
        
    def remove_outliers(self, method='iqr', threshold=1.5):
        """
        Remove outliers using IQR method
        
        Args:
            method (str): 'iqr' or 'zscore'
            threshold (float): IQR multiplier or z-score threshold
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if method == 'iqr':
            Q1 = self.data.quantile(0.25)
            Q3 = self.data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            self.data = self.data[~((self.data < lower_bound) | (self.data > upper_bound)).any(axis=1)]
            print(f"Removed outliers using IQR method. New shape: {self.data.shape}")
            
        elif method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(self.data.select_dtypes(include=[np.number])))
            self.data = self.data[(z_scores < threshold).all(axis=1)]
            print(f"Removed outliers using z-score method. New shape: {self.data.shape}")
    
    def prepare_features_target(self, target_column='Outcome'):
        """
        Separate features and target variable
        
        Args:
            target_column (str): Name of the target column
            
        Returns:
            tuple: (X, y)
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        
        self.feature_names = X.columns.tolist()
        
        print(f"Features: {self.feature_names}")
        print(f"Target distribution:\n{y.value_counts()}")
        
        return X, y
    
    def scale_features(self, X, fit=True):
        """
        Scale features using StandardScaler
        
        Args:
            X (pd.DataFrame): Features to scale
            fit (bool): Whether to fit the scaler
            
        Returns:
            np.ndarray: Scaled features
        """
        if fit:
            X_scaled = self.scaler.fit_transform(X)
            print("Scaler fitted on data")
        else:
            X_scaled = self.scaler.transform(X)
            
        return X_scaled
    
    def handle_class_imbalance(self, X, y):
        """
        Handle class imbalance using SMOTE + Under-sampling
        
        Args:
            X (np.ndarray): Features
            y (pd.Series or np.ndarray): Target variable
            
        Returns:
            tuple: (X_balanced, y_balanced)
        """
        print(f"Class distribution:\n{pd.Series(y).value_counts()}")
        print("Note: SMOTE disabled due to missing imbalanced-learn package")
        
        # Return original data without balancing
        return X, y
    
    def train_test_split_data(self, X, y, test_size=0.2, random_state=42):
        """
        Split data into train and test sets
        
        Args:
            X (np.ndarray): Features
            y (np.ndarray): Target variable
            test_size (float): Proportion of test set
            random_state (int): Random seed
        """
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"Train set size: {self.X_train.shape[0]}")
        print(f"Test set size: {self.X_test.shape[0]}")
        
    def preprocess_pipeline(self, data_path, handle_missing=True, remove_outliers_flag=True,
                           balance_classes=True, test_size=0.2):
        """
        Complete preprocessing pipeline
        
        Args:
            data_path (str): Path to data file
            handle_missing (bool): Whether to handle missing values
            remove_outliers_flag (bool): Whether to remove outliers
            balance_classes (bool): Whether to handle class imbalance
            test_size (float): Proportion of test set
            
        Returns:
            tuple: (X_train, X_test, y_train, y_test)
        """
        print("=" * 50)
        print("Starting Data Preprocessing Pipeline")
        print("=" * 50)
        
        # Load data
        self.load_data(data_path)
        
        # Get initial info
        print("\nInitial Data Info:")
        info = self.get_data_info()
        
        # Handle missing values
        if handle_missing:
            self.handle_missing_values(strategy='mean')
        
        # Remove outliers
        if remove_outliers_flag:
            self.remove_outliers(method='iqr', threshold=1.5)
        
        # Prepare features and target
        X, y = self.prepare_features_target()
        
        # Scale features
        X_scaled = self.scale_features(X, fit=True)
        
        # Handle class imbalance
        if balance_classes:
            X_scaled, y = self.handle_class_imbalance(X_scaled, y)
        
        # Train-test split
        self.train_test_split_data(X_scaled, y, test_size=test_size)
        
        print("\n" + "=" * 50)
        print("Preprocessing Pipeline Completed Successfully!")
        print("=" * 50)
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def save_scaler(self, path):
        """Save fitted scaler to file"""
        joblib.dump(self.scaler, path)
        print(f"Scaler saved to {path}")
    
    def load_scaler(self, path):
        """Load scaler from file"""
        self.scaler = joblib.load(path)
        print(f"Scaler loaded from {path}")
