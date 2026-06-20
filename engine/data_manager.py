"""
Data Manager - Central data ingestion and management module
Supportes: CSV, Excel, JSON, Parquet, SQL databases
Refactored: No Streamlit dependencies
"""
import io
import json
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text


class DataManager:
    """Handles all data ingestion, export, and basic operations."""

    SUPPORTED_FORMATS = {
        "csv": {"ext": [".csv"], "mime": "text/csv"},
        "excel": {"ext": [".xlsx", ".xls"], "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        "json": {"ext": [".json"], "mime": "application/json"},
        "parquet": {"ext": [".parquet"], "mime": "application/octet-stream"},
    }

    @staticmethod
    def detect_format(filename: str) -> str:
        """Detect file format from extension."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        for fmt, info in DataManager.SUPPORTED_FORMATS.items():
            if f".{ext}" in info["ext"]:
                return fmt
        return "unknown"

    @staticmethod
    def sample_dataframe(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
        """Return a sample of the dataframe if it exceeds max_rows."""
        if len(df) <= max_rows:
            return df
        frac = max_rows / len(df)
        return df.sample(frac=frac, random_state=42)

    @staticmethod
    def load_csv(file_bytes: bytes, encoding: str = "utf-8", sep: str = ",", 
                 decimal: str = ".", thousands: Optional[str] = None, 
                 sample_if_large: bool = True, max_rows: int = 10000) -> pd.DataFrame:
        """Load CSV file."""
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding, sep=sep, decimal=decimal,
                thousands=thousands, low_memory=False
            )
            if sample_if_large:
                df = DataManager.sample_dataframe(df, max_rows)
            return df
        except UnicodeDecodeError:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding="latin1", sep=sep, decimal=decimal,
                thousands=thousands, low_memory=False
            )
            if sample_if_large:
                df = DataManager.sample_dataframe(df, max_rows)
            return df

    @staticmethod
    def load_excel(file_bytes: bytes, sheet_name: Optional[str] = None, 
                   header: int = 0, sample_if_large: bool = True, 
                   max_rows: int = 10000):
        """Load Excel file."""
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        available_sheets = xl.sheet_names

        if sheet_name is None or sheet_name not in available_sheets:
            sheet_name = available_sheets[0]

        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=header)
        
        if sample_if_large:
            df = DataManager.sample_dataframe(df, max_rows)
            
        return df, available_sheets

    @staticmethod
    def load_json(file_bytes: bytes, orient: Optional[str] = None, 
                  lines: bool = False, sample_if_large: bool = True, 
                  max_rows: int = 10000) -> pd.DataFrame:
        """Load JSON file."""
        content = file_bytes.decode('utf-8')

        if lines:
            df = pd.read_json(io.StringIO(content), lines=True)
        else:
            data = json.loads(content)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.json_normalize(data)
            else:
                df = pd.DataFrame([data])
        
        if sample_if_large:
            df = DataManager.sample_dataframe(df, max_rows)
            
        return df

    @staticmethod
    def load_parquet(file_bytes: bytes, sample_if_large: bool = True, 
                     max_rows: int = 10000) -> pd.DataFrame:
        """Load Parquet file."""
        df = pd.read_parquet(io.BytesIO(file_bytes))
        
        if sample_if_large:
            df = DataManager.sample_dataframe(df, max_rows)
            
        return df

    @staticmethod
    def load_from_sql(connection_string: str, table_name: str, 
                      where_clause: Optional[str] = None,
                      max_rows: int = 10000) -> pd.DataFrame:
        """Load data from SQL database with parameterized queries."""
        # Whitelist table name against known tables for security
        engine = create_engine(connection_string)
        safe_tables = DataManager.get_sql_tables(connection_string)
        
        if table_name not in safe_tables:
            raise ValueError(f"Table '{table_name}' not in allowed list or does not exist")
        
        # Use parameterized query to prevent SQL injection
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += " LIMIT :limit"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params={"limit": max_rows})
            
        return df

    @staticmethod
    def get_sql_tables(connection_string: str) -> List[str]:
        """Get list of tables from SQL database."""
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            tables = pd.read_sql(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"), conn)
        return tables.iloc[:, 0].tolist() if not tables.empty else []

    @staticmethod
    def auto_convert_types(df: pd.DataFrame) -> pd.DataFrame:
        """Automatically detect and convert column types."""
        df = df.copy()

        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                continue

            if df[col].dtype == 'object':
                try:
                    converted = pd.to_datetime(df[col], errors='raise', infer_datetime_format=True)
                    if converted.notna().sum() / len(df) > 0.8:
                        df[col] = converted
                        continue
                except:
                    pass

                try:
                    converted = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('%', ''), errors='coerce')
                    if converted.notna().sum() / len(df) > 0.8:
                        df[col] = converted
                        continue
                except:
                    pass

                if df[col].nunique() / len(df) < 0.05 and df[col].nunique() < 100:
                    df[col] = df[col].astype('category')

        return df

    @staticmethod
    def get_sample_data() -> pd.DataFrame:
        """Generate sample dataset for demo purposes."""
        np.random.seed(42)
        n = 1000

        df = pd.DataFrame({
            'customer_id': range(1000, 2000),
            'age': np.random.randint(18, 80, n),
            'gender': np.random.choice(['Male', 'Female', 'Other'], n, p=[0.48, 0.48, 0.04]),
            'income': np.random.lognormal(10.8, 0.5, n).round(2),
            'signup_date': pd.date_range('2020-01-01', periods=n, freq='D').to_series().sample(n, replace=True).values,
            'purchase_amount': np.random.exponential(150, n).round(2),
            'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Home', 'Sports'], n),
            'satisfaction': np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.1, 0.2, 0.35, 0.3]),
            'is_premium': np.random.choice([True, False], n, p=[0.2, 0.8]),
            'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'], n),
        })

        # Add some missing values
        missing_idx = np.random.choice(df.index, size=int(n * 0.05), replace=False)
        df.loc[missing_idx, 'income'] = np.nan

        missing_idx2 = np.random.choice(df.index, size=int(n * 0.03), replace=False)
        df.loc[missing_idx2, 'satisfaction'] = np.nan

        # Add some outliers
        outlier_idx = np.random.choice(df.index, size=20, replace=False)
        df.loc[outlier_idx, 'purchase_amount'] = df['purchase_amount'].max() * 5

        return df

    @staticmethod
    def get_titanic_data() -> pd.DataFrame:
        """Generate Titanic-like sample dataset."""
        np.random.seed(42)
        n = 891
        
        df = pd.DataFrame({
            'PassengerId': range(1, n + 1),
            'Survived': np.random.choice([0, 1], n, p=[0.62, 0.38]),
            'Pclass': np.random.choice([1, 2, 3], n, p=[0.24, 0.21, 0.55]),
            'Age': np.concatenate([
                np.random.normal(30, 15, int(n * 0.8)),
                np.full(int(n * 0.2), np.nan)
            ]),
            'SibSp': np.random.choice([0, 1, 2, 3, 4, 5, 8], n, p=[0.68, 0.23, 0.03, 0.03, 0.01, 0.01, 0.01]),
            'Parch': np.random.choice([0, 1, 2, 3, 4, 5, 6], n, p=[0.76, 0.13, 0.08, 0.01, 0.01, 0.005, 0.005]),
            'Fare': np.random.exponential(30, n).round(2),
            'Sex': np.random.choice(['male', 'female'], n, p=[0.65, 0.35]),
            'Embarked': np.random.choice(['S', 'C', 'Q'], n, p=[0.72, 0.19, 0.09]),
        })
        
        # Add some missing values
        missing_idx = np.random.choice(df.index, size=int(n * 0.02), replace=False)
        df.loc[missing_idx, 'Embarked'] = np.nan
        
        return df

    @staticmethod
    def get_wine_data() -> pd.DataFrame:
        """Generate Wine quality-like sample dataset."""
        np.random.seed(42)
        n = 1000
        
        df = pd.DataFrame({
            'fixed_acidity': np.random.normal(8.3, 1.5, n).round(2),
            'volatile_acidity': np.random.normal(0.52, 0.15, n).round(3),
            'citric_acid': np.random.normal(0.27, 0.1, n).round(2),
            'residual_sugar': np.random.exponential(2.5, n).round(2),
            'chlorides': np.random.normal(0.087, 0.047, n).round(3),
            'free_sulfur_dioxide': np.random.normal(35, 15, n).round(1),
            'total_sulfur_dioxide': np.random.normal(138, 42, n).round(1),
            'density': np.random.normal(0.997, 0.003, n).round(5),
            'pH': np.random.normal(3.31, 0.15, n).round(2),
            'sulphates': np.random.normal(0.66, 0.17, n).round(3),
            'alcohol': np.random.normal(10.4, 1.1, n).round(2),
            'quality': np.random.choice([3, 4, 5, 6, 7, 8, 9], n, p=[0.02, 0.08, 0.35, 0.35, 0.15, 0.04, 0.01]),
        })
        
        return df

    @staticmethod
    def get_iris_data() -> pd.DataFrame:
        """Generate Iris-like sample dataset."""
        np.random.seed(42)
        n_per_class = 50
        
        setosa_sepal_length = np.random.normal(5.0, 0.35, n_per_class)
        setosa_sepal_width = np.random.normal(3.4, 0.38, n_per_class)
        setosa_petal_length = np.random.normal(1.5, 0.17, n_per_class)
        setosa_petal_width = np.random.normal(0.25, 0.11, n_per_class)
        
        versicolor_sepal_length = np.random.normal(5.9, 0.52, n_per_class)
        versicolor_sepal_width = np.random.normal(2.8, 0.31, n_per_class)
        versicolor_petal_length = np.random.normal(4.3, 0.47, n_per_class)
        versicolor_petal_width = np.random.normal(1.3, 0.20, n_per_class)
        
        virginica_sepal_length = np.random.normal(6.6, 0.64, n_per_class)
        virginica_sepal_width = np.random.normal(3.0, 0.32, n_per_class)
        virginica_petal_length = np.random.normal(5.6, 0.55, n_per_class)
        virginica_petal_width = np.random.normal(2.0, 0.27, n_per_class)
        
        df = pd.DataFrame({
            'sepal_length': np.concatenate([setosa_sepal_length, versicolor_sepal_length, virginica_sepal_length]).round(2),
            'sepal_width': np.concatenate([setosa_sepal_width, versicolor_sepal_width, virginica_sepal_width]).round(2),
            'petal_length': np.concatenate([setosa_petal_length, versicolor_petal_length, virginica_petal_length]).round(2),
            'petal_width': np.concatenate([setosa_petal_width, versicolor_petal_width, virginica_petal_width]).round(2),
            'species': ['setosa'] * n_per_class + ['versicolor'] * n_per_class + ['virginica'] * n_per_class,
        })
        
        return df

    @staticmethod
    def export_to_formats(df: pd.DataFrame, base_name: str = "export") -> Dict[str, bytes]:
        """Export dataframe to multiple formats."""
        exports = {}

        # CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        exports["csv"] = csv_buffer.getvalue().encode()

        # Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Data']

            header_format = workbook.add_format({
                'bold': True, 'bg_color': '#00D4AA',
                'font_color': '#0E1117', 'border': 1
            })

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                max_len = max(df[value].astype(str).map(len).max(), len(str(value))) + 2
                worksheet.set_column(col_num, col_num, min(max_len, 50))

        exports["excel"] = excel_buffer.getvalue()

        # JSON
        exports["json"] = df.to_json(orient='records', indent=2).encode()

        # Parquet
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        exports["parquet"] = parquet_buffer.getvalue()

        # HTML
        html_buffer = io.StringIO()
        df.to_html(html_buffer, index=False)
        exports["html"] = html_buffer.getvalue().encode()

        return exports
