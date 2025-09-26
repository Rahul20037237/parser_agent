import sys
import pandas as pd
sys.path.append(r'D:\WORKSPACE\agents')
try:
    from settings import settings
except ImportError:
    from .settings import settings
from pydantic import BaseModel
from pathlib import Path
import subprocess
from typing import Annotated, List, Dict , Optional ,ClassVar
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, CSVLoader , PythonLoader



class Prompt:
    instruct=""
    tags={}


class Code_exe(BaseModel):
    file_path: Optional[Path]=None
    Code: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

class Logic_err(BaseModel):
    error: Optional[str] = None
    sample_data : Optional[Dict] = None

class Parser_agent:
    def __init__(self, dir_path: str):
        self.llm = ChatGroq(model=settings.MODEL_NAME, api_key=settings.API_KEY.get_secret_value(), temperature=0)
        self.path = Path(dir_path)
        if not self.path.is_dir() or not self.path.exists():
            raise ValueError("Invalid directory path")
        self.files = list(self.path.glob("*.pdf")) + list(self.path.glob("*.csv"))
        if not self.files:
            raise ValueError("No files found in the directory")
        
        
    def read_file(self):
        try:
           for files in self.files:
              if files.suffix.lower() == ".pdf":
                  Loader = PyPDFLoader(str(files))
                  docs = Loader.load()
                  text = "\n".join([doc.page_content for i, doc in enumerate(docs)])
                  yield text
              else:
                  Loader = CSVLoader(str(files))
                  docs = Loader.load()
                  text = "".join([f"<line {i}>{doc.page_content}</line {i}>" for i, doc in enumerate(docs)])
                  yield {'file_name': files, 'text': text}
        except Exception as e:
            print(e)
            return None
        
                
    def code_executor_and_checker(self, code: str , dir_path: Path,file_name: str) -> bool:
        try: 
            dir_path.mkdir(parents=True,exist_ok=True)
            file_path=dir_path / f"{file_name}.py"
            file_path.write_text(code)
            venv_python = Path(r"C:\Users\rohith\Envs\CRUD\Scripts\python.exe") 
            sample_pdf=r"C:\Users\rohith\Downloads\ai-agent-challenge-main\ai-agent-challenge-main\data\icici\icici sample.pdf"
            result=subprocess.run([venv_python, str(file_path)],input=sample_pdf, capture_output=True, text=True)
            
            # print(result.stderr)
            return (False,result,file_path) if result.stderr else (True,result,file_path)
        except Exception as e:
            print(e)
    
    
    def write_code(self,**kwargs):
        prompt=Prompt.instruct.format(**kwargs)
        answer=self.llm.invoke(prompt)
        return answer.content
    
    @staticmethod
    def load_prompt(file_name: str) -> str:
        path = Path(file_name)
        text=path.read_text(encoding="utf-8")
        return text
            
        
    def logic_check(self,org_csv:Path,gen_csv:Path):
        if not gen_csv.exists():
            Logic_err.error = " File is not Found"
            return False
        if not org_csv.exists():
            raise ValueError("Original Csv is not found")
        org_data=pd.read_csv(org_csv)
        gen_data=pd.read_csv(gen_csv)
        diff_cols = org_data.columns[org_data.ne(gen_data).any()]
        print(diff_cols.empty)
        if not diff_cols.empty:
            Logic_err.error =f"Column mistmatch {diff_cols}"
            Logic_err.sample_data = f"{org_data.head(3)}"
            return False
        diff_rows = org_data[org_data[diff_cols].ne(gen_data[diff_cols]).any(axis=1)]
        print(diff_rows)
        if not diff_rows.empty:
            Logic_err.error = f"Data mismatch {diff_rows}"
            Logic_err.sample_data = f"{org_data.head(3)}"
            return False
        return True
    
    def optimizer(self,file_path: Path ,Error: Code_exe|Logic_err):
        python_file = PythonLoader(file_path)
        docs=python_file.load()
        answer=self.write_code(code=docs,error=Error.error)
        return answer
    
    def generated_the_textcases(self,file_path: Path,file_name:str):
        python_file = PythonLoader(file_path)
        code=python_file.load()
        answer=self.write_code(code=code)
        result=self.code_executor_and_checker(code=answer,
                                       dir_path=r'D:\WORKSPACE\agents\Testing\Gen_test',
                                       file_name=file_name)
        return answer