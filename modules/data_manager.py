"""
Data Manager - Central data ingestion and management module
Supportes: CSV, Excel, JSON, Parquet, SQL databases
"""
import io
import json
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

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
        else:
            # Calculate sampling fraction
            frac = max_rows / len(df)
            return df.sample(frac=frac, random_state=42)

    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_csv(file_bytes: bytes, encoding: str = "utf-8", sep: str = ",", 
                 decimal: str = ".", thousands: Optional[str] = None, 
                 sample_if_large: bool = True, max_rows: int = 10000) -> pd.DataFrame:
        """Load CSV file with caching."""
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
                sep=sep,
                decimal=decimal,
                thousands=thousands,
                low_memory=False
            )
            
            if sample_if_large:
                df = DataManager.sample_dataframe(df, max_rows)
                
            return df
        except UnicodeDecodeError:
            # Try with different encoding
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding="latin1",
                sep=sep,
                decimal=decimal,
                thousands=thousands,
                low_memory=False
            )
            
            if sample_if_large:
                df = DataManager.sample_dataframe(df, max_rows)
                
            return df

    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_excel(file_bytes: bytes, sheet_name: Optional[str] = None, 
                   header: int = 0, sample_if_large: bool = True, 
                   max_rows: int = 10000) -> pd.DataFrame:
        """Load Excel file with caching."""
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        available_sheets = xl.sheet_names

        if sheet_name is None or sheet_name not in available_sheets:
            sheet_name = available_sheets[0]

        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=header)
        
        if sample_if_large:
            df = DataManager.sample_dataframe(df, max_rows)
            
        return df, available_sheets

    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_json(file_bytes: bytes, orient: Optional[str] = None, 
                  lines: bool = False, sample_if_large: bool = True, 
                  max_rows: int = 10000) -> pd.DataFrame:
        """Load JSON file with caching."""
        content = file_bytes.decode('utf-8')

        if lines:
            df = pd.read_json(io.StringIO(content), lines=True)
        else:
            data = json.loads(content)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try to normalize nested JSON
                df = pd.json_normalize(data)
            else:
                df = pd.DataFrame([data])
        
        if sample_if_large:
            df = DataManager.sample_dataframe(df, max_rows)
            
        return df

    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_parquet(file_bytes: bytes, sample_if_large: bool = True, 
                     max_rows: int = 10000) -> pd.DataFrame:
        """Load Parquet file with caching."""
        df = pd.read_parquet(io.BytesIO(file_bytes))
        
        if sample_if_large:
            df = DataManager.sample_dataframe(df, max_rows)
            
        return df

    @staticmethod
    def load_from_sql(connection_string: str, query: str, sample_if_large: bool = True, 
                      max_rows: int = 10000) -> pd.DataFrame:
        """Load data from SQL database."""
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            
        if sample_if_large:
            df = DataManager.sample_dataframe(df, max_rows)
            
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
            # Skip if already datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                continue

            # Try datetime conversion
            if df[col].dtype == 'object':
                try:
                    converted = pd.to_datetime(df[col], errors='raise', infer_datetime_format=True)
                    if converted.notna().sum() / len(df) > 0.8:  # 80% success rate
                        df[col] = converted
                        continue
                except:
                    pass

                # Try numeric conversion
                try:
                    converted = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('%', ''), errors='coerce')
                    if converted.notna().sum() / len(df) > 0.8:
                        df[col] = converted
                        continue
                except:
                    pass

                # Categorical for low cardinality
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

            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#00D4AA',
                'font_color': '#0E1117',
                'border': 1
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

        # Feather
        feather_buffer = io.BytesIO()
        df.to_feather(feather_buffer)
        exports["feather"] = feather_buffer.getvalue()

        # HTML
        html_buffer = io.StringIO()
        df.to_html(html_buffer, index=False)
        exports["html"] = html_buffer.getvalue().encode()

        # LaTeX
        try:
            latex_str = df.to_latex(index=False)
            exports["latex"] = latex_str.encode()
        except:
            # If pandas can't generate LaTeX, provide a basic table
            exports["latex"] = DataManager._generate_basic_latex(df).encode()

        return exports

    @staticmethod
    def _generate_basic_latex(df: pd.DataFrame) -> str:
        """Generate basic LaTeX table."""
        # Convert all values to strings to avoid formatting issues
        df_str = df.astype(str)
        
        # Start LaTeX table
        latex = "\\begin{tabular}{|" + "c|"*len(df.columns) + "}\n\\hline\n"
        
        # Add header
        latex += " & ".join(df.columns) + " \\\\\n\\hline\n"
        
        # Add data rows
        for idx, row in df_str.iterrows():
            latex += " & ".join(row.values) + " \\\\\n"
        
        latex += "\\hline\n\\end{tabular}"
        
        return latex