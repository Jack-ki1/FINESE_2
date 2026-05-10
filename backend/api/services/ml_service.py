import pandas as pd
import numpy as np
import pickle
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, classification_report

from .dataset_service import DatasetService

class MlService:
    def __init__(self):
        self.dataset_service = DatasetService()
        self.models: Dict[str, Any] = {}
        self.model_info: Dict[str, Dict[str, Any]] = {}
    
    async def initiate_training(
        self, 
        dataset_id: str, 
        target_column: str, 
        model_type: str = "auto", 
        features: Optional[List[str]] = None, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Initiate model training and return model ID"""
        model_id = str(uuid.uuid4())
        
        self.model_info[model_id] = {
            "model_id": model_id,
            "dataset_id": dataset_id,
            "target_column": target_column,
            "model_type": model_type,
            "features": features,
            "parameters": parameters or {},
            "status": "initialized",
            "created_at": datetime.now(),
            "trained_at": None,
            "metrics": None
        }
        
        return model_id
    
    async def perform_training(self, model_id: str):
        """Perform the actual training in the background"""
        try:
            # Update status
            self.model_info[model_id]["status"] = "training"
            
            # Get dataset
            dataset_id = self.model_info[model_id]["dataset_id"]
            df = self.dataset_service.datasets.get(dataset_id)
            
            if df is None:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            target_column = self.model_info[model_id]["target_column"]
            features = self.model_info[model_id]["features"]
            model_type = self.model_info[model_id]["model_type"]
            parameters = self.model_info[model_id]["parameters"]
            
            # Prepare features and target
            if features is None:
                # Use all columns except target
                feature_columns = [col for col in df.columns if col != target_column]
            else:
                feature_columns = [col for col in features if col in df.columns and col != target_column]
            
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Handle categorical features
            encoders = {}
            for col in X.select_dtypes(include=['object']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                encoders[col] = le
            
            # Handle categorical target if needed
            target_encoder = None
            if y.dtype == 'object':
                target_encoder = LabelEncoder()
                y = target_encoder.fit_transform(y.astype(str))
            
            # Split the data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Determine if this is a classification or regression problem
            if model_type == "auto":
                if len(np.unique(y)) < 0.05 * len(y):  # Heuristic for classification
                    model_type = "classification"
                else:
                    model_type = "regression"
            
            # Select and initialize model
            if model_type == "classification":
                if "RandomForest" in str(parameters.get("algorithm", "")):
                    model = RandomForestClassifier(**{k: v for k, v in parameters.items() if k != "algorithm"}, random_state=42)
                elif "LogisticRegression" in str(parameters.get("algorithm", "")):
                    model = LogisticRegression(**{k: v for k, v in parameters.items() if k != "algorithm"}, random_state=42)
                else:
                    model = RandomForestClassifier(random_state=42, n_estimators=100)
            else:  # regression
                if "RandomForest" in str(parameters.get("algorithm", "")):
                    model = RandomForestRegressor(**{k: v for k, v in parameters.items() if k != "algorithm"}, random_state=42)
                elif "LinearRegression" in str(parameters.get("algorithm", "")):
                    model = LinearRegression(**{k: v for k, v in parameters.items() if k != "algorithm"})
                else:
                    model = RandomForestRegressor(random_state=42, n_estimators=100)
            
            # Train the model
            model.fit(X_train, y_train)
            
            # Make predictions on test set
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            if model_type == "classification":
                accuracy = accuracy_score(y_test, y_pred)
                metrics = {
                    "accuracy": float(accuracy),
                    "classification_report": classification_report(y_test, y_pred, output_dict=True)
                }
            else:  # regression
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mse)
                metrics = {
                    "mse": float(mse),
                    "rmse": float(rmse),
                    "r2": float(r2)
                }
            
            # Store the model and metadata
            self.models[model_id] = {
                "model": model,
                "encoders": encoders,
                "target_encoder": target_encoder,
                "feature_columns": feature_columns,
                "model_type": model_type
            }
            
            # Update model info
            self.model_info[model_id]["status"] = "trained"
            self.model_info[model_id]["trained_at"] = datetime.now()
            self.model_info[model_id]["metrics"] = metrics
            
        except Exception as e:
            self.model_info[model_id]["status"] = "failed"
            self.model_info[model_id]["error"] = str(e)
    
    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a trained model"""
        if model_id not in self.model_info:
            return None
        
        return self.model_info[model_id]
    
    async def make_predictions(self, model_id: str, data: List[Dict[str, Any]]) -> List[Any]:
        """Make predictions using a trained model"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found or not trained yet")
        
        model_data = self.models[model_id]
        model = model_data["model"]
        encoders = model_data["encoders"]
        target_encoder = model_data["target_encoder"]
        feature_columns = model_data["feature_columns"]
        
        # Convert input data to DataFrame
        X = pd.DataFrame(data)
        
        # Ensure all required features are present
        for col in feature_columns:
            if col not in X.columns:
                raise ValueError(f"Required feature '{col}' not provided in input data")
        
        # Select and order features
        X = X[feature_columns]
        
        # Apply the same encoding as during training
        for col, encoder in encoders.items():
            if col in X.columns:
                X[col] = encoder.transform(X[col].astype(str))
        
        # Make predictions
        predictions = model.predict(X)
        
        # If we encoded the target, reverse the encoding
        if target_encoder is not None:
            predictions = target_encoder.inverse_transform(predictions.astype(int))
        
        return predictions.tolist()
    
    async def get_model_bytes(self, model_id: str) -> Optional[bytes]:
        """Get the trained model as bytes for download"""
        if model_id not in self.models:
            return None
        
        model_data = self.models[model_id]
        
        # Create a serializable object containing the model and metadata
        serializable_model = {
            "model": model_data["model"],
            "encoders": model_data["encoders"],
            "target_encoder": model_data["target_encoder"],
            "feature_columns": model_data["feature_columns"],
            "model_type": model_data["model_type"],
            "model_info": self.model_info[model_id]
        }
        
        return pickle.dumps(serializable_model)