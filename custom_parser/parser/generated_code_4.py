import re
import pandas as pd
from pathlib import Path

class BankStatementParser:
    def __init__(self, file_path: str):
        """
        Initialize the parser with a file path containing the bank statement text.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        self.text = path.read_text(encoding="utf-8")
        self.headers = []
        self.rows = []

    def parse_text(self) -> pd.DataFrame:
        """Parse text into headers and rows"""
        lines = self.text.strip().split("\n")
        if not lines:
            raise ValueError("Input text is empty")
        
        # Check if the text is a bank statement
        if "Date" not in lines[0] and "Description" not in lines[0]:
            return "Not a bank statement. No code generated."
        
        # Extract headers (first line) and normalize spaces/tabs
        self.headers = re.split(r"\s+|\t+", lines[0].strip())
        
        # Extract rows
        self.rows = [re.split(r"\s+|\t+", line.strip()) for line in lines[1:]]
        
        # Fill missing values with empty string
        self.rows = [[col if col else "" for col in row] for row in self.rows]
        
        return pd.DataFrame(self.rows, columns=self.headers)

    def save_to_csv(self, save_path: str, filename: str) -> pd.DataFrame:
        """Save parsed DataFrame to CSV"""
        df = self.parse_text()
        path = Path(save_path)
        path.mkdir(parents=True, exist_ok=True)
        df.to_csv(path / f"{filename}.csv", index=False)
        return df

# --- Usage Example ---
parser = BankStatementParser(r"C:\Users\user\Documents\statement.pdf")
df = parser.save_to_csv(r"D:\WORKSPACE\agents\custom_parser\parser", "icici_paraser")
print(df)