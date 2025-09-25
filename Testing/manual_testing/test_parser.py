import sys
from pathlib import Path
import pytest
sys.path.append(r'D:\WORKSPACE\agents')
from paraser_agent import Parser_agent,Code_exe,Logic_err

SAMPLE_CSV=Path(r'D:\WORKSPACE\agents\Testing\sample.csv')
CUSTOM_PATH=Path(r'D:\WORKSPACE\agents\custom_parser\parser\icici')
FILE_NAME='sample_test'
SAMPLE_CODE="""import pandas as pd

data = {
    "Name": ["Alice", "Bob", "Charlie", "David"],
    "Age": [25, 30, 35, 40],
    "City": ["New York", "London", "Paris", "Berlin"]
}

df = pd.DataFrame(data)
df.to_csv("sample.csv", index=False)
"""

@pytest.fixture
def agent():
    return Parser_agent(str(r'C:\Users\rohith\Downloads\ai-agent-challenge-main\ai-agent-challenge-main\data\icici'))

def test_read_file(agent):
    value=agent.read_file()
    for i in value:
        assert i is not None
        
def test_code_executor(agent):
    result=agent.code_executor_and_checker(SAMPLE_CODE,CUSTOM_PATH,FILE_NAME)
    print(Code_exe)
    assert result
def test_logic(agent):
    result=agent.logic_check(SAMPLE_CSV,SAMPLE_CSV)
    assert result is True
