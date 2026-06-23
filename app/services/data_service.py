"""
FINESE2 - Data Service Layer
Business logic for data operations, file handling, and dataset management.
"""
import pandas as pd
import os
from typing import Optional, Dict, Any, List
from app.models.user import User, Dataset
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class DataService:
    """
    Service class for data-related operations.
    
    This service layer separates business logic from route handlers,
    making the code more testable and maintainable.
    """
    
    @staticmethod
    def upload_file(file, user_id: int, filename: str, sample_if_large: bool = True, 
                   max_rows: int = 10000) -> Dict[str, Any]:
        """
        Handle file upload and create dataset record.
        
        Args:
            file: FileStorage object from Flask request
            user_id: ID of the user uploading the file
            filename: Original filename
            sample_if_large: Whether to sample large datasets
            max_rows: Maximum rows to load
            
        Returns:
            Dictionary with dataset information
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Create upload directory if it doesn't exist
            upload_folder = os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'dashboard',
                'uploads'
            )
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate safe filename (prevent path traversal attacks)
            safe_filename = os.path.basename(filename)
            file_path = os.path.join(upload_folder, safe_filename)
            
            # Save file
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Load and analyze file based on extension
            ext = safe_filename.rsplit('.', 1)[-1].lower() if '.' in safe_filename else ''
            
            if ext == 'csv':
                df = pd.read_csv(file_path, nrows=max_rows if sample_if_large else None)
            elif ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path, nrows=max_rows if sample_if_large else None)
            elif ext == 'json':
                df = pd.read_json(file_path, nrows=max_rows if sample_if_large else None)
            elif ext == 'parquet':
                df = pd.read_parquet(file_path)
                if sample_if_large and len(df) > max_rows:
                    df = df.sample(n=max_rows, random_state=42)
            else:
                # Try CSV as default
                df = pd.read_csv(file_path, nrows=max_rows if sample_if_large else None)
            
            # Create dataset record in database
            dataset = Dataset(
                name=safe_filename,
                file_path=file_path,
                owner_id=user_id,
                rows=len(df),
                columns=len(df.columns),
                file_size=file_size
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            logger.info(f"Dataset uploaded: {safe_filename} by user {user_id}")
            
            return {
                'dataset_id': dataset.id,
                'filename': safe_filename,
                'shape': list(df.shape),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to upload file: {e}")
            raise
    
    @staticmethod
    def get_user_datasets(user_id: int) -> List[Dict[str, Any]]:
        """
        Get all datasets owned by a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of dataset dictionaries
        """
        datasets = Dataset.query.filter_by(owner_id=user_id).order_by(Dataset.created_at.desc()).all()
        return [d.to_dict() for d in datasets]
    
    @staticmethod
    def get_dataset(dataset_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific dataset (only if owned by user).
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Dataset dictionary or None if not found/not owned
        """
        dataset = Dataset.query.get(dataset_id)
        
        if not dataset or dataset.owner_id != user_id:
            return None
        
        return dataset.to_dict()
    
    @staticmethod
    def delete_dataset(dataset_id: int, user_id: int) -> bool:
        """
        Delete a dataset (only if owned by user).
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID (for ownership verification)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        dataset = Dataset.query.get(dataset_id)
        
        # Verify ownership
        if not dataset or dataset.owner_id != user_id:
            return False
        
        try:
            # Delete physical file
            if os.path.exists(dataset.file_path):
                os.remove(dataset.file_path)
                logger.info(f"Deleted file: {dataset.file_path}")
            
            # Delete database record
            db.session.delete(dataset)
            db.session.commit()
            
            logger.info(f"Dataset deleted: {dataset.name} by user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete dataset: {e}")
            return False
    
    @staticmethod
    def save_cleaned_dataset(df: pd.DataFrame, user_id: int, original_dataset_id: int,
                           summary: Dict) -> Dict[str, Any]:
        """
        Save a cleaned version of a dataset.
        
        Args:
            df: Cleaned DataFrame
            user_id: User ID
            original_dataset_id: Original dataset ID
            summary: Cleaning operation summary
            
        Returns:
            Dictionary with new dataset information
        """
        try:
            original_dataset = Dataset.query.get(original_dataset_id)
            if not original_dataset or original_dataset.owner_id != user_id:
                raise ValueError("Original dataset not found or access denied")
            
            # Create upload directory
            upload_folder = os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'dashboard',
                'uploads'
            )
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate filename for cleaned dataset
            original_name = original_dataset.name.rsplit('.', 1)[0]
            cleaned_filename = f"{original_name}_cleaned.csv"
            file_path = os.path.join(upload_folder, cleaned_filename)
            
            # Save cleaned dataframe
            df.to_csv(file_path, index=False)
            file_size = os.path.getsize(file_path)
            
            # Create new dataset record
            cleaned_dataset = Dataset(
                name=cleaned_filename,
                file_path=file_path,
                owner_id=user_id,
                rows=len(df),
                columns=len(df.columns),
                file_size=file_size,
                parent_id=original_dataset_id  # Link to original
            )
            
            db.session.add(cleaned_dataset)
            db.session.commit()
            
            logger.info(f"Cleaned dataset saved: {cleaned_filename} by user {user_id}")
            
            return {
                'dataset_id': cleaned_dataset.id,
                'filename': cleaned_filename,
                'rows': len(df),
                'columns': len(df.columns)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save cleaned dataset: {e}")
            raise
    
    @staticmethod
    def load_sample_dataset(dataset_name: str, user_id: int) -> Dict[str, Any]:
        """
        Load a built-in sample dataset.
        
        Args:
            dataset_name: Name of sample dataset (iris, titanic, wine, etc.)
            user_id: User ID
            
        Returns:
            Dictionary with dataset information
        """
        try:
            import seaborn as sns
            
            # Load sample dataset
            if dataset_name == 'iris':
                df = sns.load_dataset('iris')
            elif dataset_name == 'titanic':
                df = sns.load_dataset('titanic')
            elif dataset_name == 'wine':
                df = sns.load_dataset('wine')
            elif dataset_name == 'tips':
                df = sns.load_dataset('tips')
            # Dashboard compatibility names
            elif dataset_name in ['default', 'customers']:
                # No dedicated “customers” dataset in seaborn; use tips as a mixed-tabular fallback.
                df = sns.load_dataset('tips')
            else:
                raise ValueError(f"Unknown sample dataset: {dataset_name}")

            
            # Create upload directory
            upload_folder = os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'dashboard',
                'uploads'
            )
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save as CSV
            filename = f"{dataset_name}.csv"
            file_path = os.path.join(upload_folder, filename)
            df.to_csv(file_path, index=False)
            file_size = os.path.getsize(file_path)
            
            # Create dataset record
            dataset = Dataset(
                name=filename,
                file_path=file_path,
                owner_id=user_id,
                rows=len(df),
                columns=len(df.columns),
                file_size=file_size
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            logger.info(f"Sample dataset loaded: {dataset_name} by user {user_id}")
            
            return {
                'dataset_id': dataset.id,
                'filename': filename,
                'shape': list(df.shape),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2)
            }
            
        except ImportError:
            raise ValueError("seaborn package required for sample datasets. Install with: pip install seaborn")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to load sample dataset: {e}")
            raise
    
    @staticmethod
    def load_dataframe(dataset_id: int, user_id: int) -> Optional[pd.DataFrame]:
        """
        Load a dataset into a pandas DataFrame (with ownership check).
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID (for ownership verification)
            
        Returns:
            pandas DataFrame or None if not accessible
        """
        dataset = Dataset.query.get(dataset_id)
        
        if not dataset or dataset.owner_id != user_id:
            return None
        
        if not os.path.exists(dataset.file_path):
            logger.error(f"File not found: {dataset.file_path}")
            return None
        
        try:
            ext = dataset.name.rsplit('.', 1)[-1].lower() if '.' in dataset.name else ''
            
            if ext == 'csv':
                return pd.read_csv(dataset.file_path)
            elif ext in ['xlsx', 'xls']:
                return pd.read_excel(dataset.file_path)
            elif ext == 'json':
                return pd.read_json(dataset.file_path)
            elif ext == 'parquet':
                return pd.read_parquet(dataset.file_path)
            else:
                return pd.read_csv(dataset.file_path)
                
        except Exception as e:
            logger.error(f"Failed to load dataframe: {e}")
            return None


# Singleton instance for easy import
data_service = DataService()
