import sys
sys.path.append(r'D:\WORKSPACE\agents')
try:
    from paraser_agent import Parser_agent, Code_exe, Logic_err, Prompt
except ImportError as e:
    from .paraser_agent import Parser_agent, Code_exe, Logic_err, Prompt
    
from pathlib import Path
from langgraph.graph import StateGraph
from pydantic import BaseModel, PrivateAttr
from typing import List, Optional

GEN_PATH = Path(r'D:\WORKSPACE\agents\custom_parser\parser')
DIR_PATH = Path(r'C:\Users\rohith\Downloads\ai-agent-challenge-main\ai-agent-challenge-main\data\icici')
TEST_DATA = Path(r'D:\WORKSPACE\agents\Testing\test_data\result.csv')

agent=Parser_agent(DIR_PATH)
Code_exec=Code_exe()
Logic_errc=Logic_err()
Promptc=Prompt()

class State(BaseModel):
    Node: Optional[List[str]] = None
    Status: Optional[List[str]] = None
    Dir_path: Optional[str] = None
    text: Optional[str] = None
    tries: Optional[int] = 0



def preprocessing(state: State):
    agent = Parser_agent(dir_path=state.Dir_path)
    file_reader = agent.read_file()
    state.Status = [file_reader.__class__.__name__]
    state.Node = ['preprocessing']
    state.text = next(file_reader)
    return state

def planner(state: State):
    state.Node.append('planner')
    
    if state.tries > 3:
        return 'END'
    state.tries += 1
    
    if Code_exec.file_path is None:
        Promptc.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\code_generated.txt')
        return 'Generate_code'
    else:
        if Code_exec.error:
            Promptc.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\code_error.txt')
            return 'Evaluator'
        elif Logic_errc.error:
            Promptc.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\logic_error.txt')
            return 'Evaluator'
        else:
            Promptc.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\test_case.txt')
            return 'Generate_test_cases'

def Generate_code(state: State):
    state.Node.append('Generate_code')
    code = agent.write_code(text=state.text['text'])
    state.Status.append("Write_code")
    Code_exec.Code = code
    state.text = code
    print('done')
    return state

def Evaluator(state: State):
    state.Node.append('Evaluator')
    
    # Execute the code and check for errors
    file_name = f"generated_code_{state.tries}"
    success = agent.code_executor_and_checker(
        code=Code_exec.Code,
        dir_path=GEN_PATH,
        file_name=file_name
    )
    
    if not success and Code_exec.error:
        state.Status.append("Code_execution_failed")
        return 'Code_check'
    
    if success and Code_exec.file_path:
        generated_csv = GEN_PATH / "output.csv" 
        original_csv = TEST_DATA
        
        logic_success = agent.logic_check(original_csv, generated_csv)
        
        if not logic_success:
            state.Status.append("Logic_check_failed")
            return 'Logic_check'
        else:
            state.Status.append("All_checks_passed")
            return 'Generate_test_cases'
    
    return 'planner'

def code_check(state: State):
    state.Node.append('Code_check')
    if Code_exec.error:
        # Fix the code using the optimizer
        fixed_code = agent.optimizer(
            file_path=Code_exec.file_path,
            Error=Code_exec.error
        )
        state.text = fixed_code
        Code_exec.Code = fixed_code
        Code_exec.error = None  # Reset error
        state.Status.append("Code_fixed")
    return state

def logic_check(state: State):
    state.Node.append('Logic_check')
    if Logic_errc.error:
        # Optimize the logic using the optimizer
        optimizer_result = agent.optimizer(
            file_path=Code_exec.file_path,
            Error=Logic_errc
        )
        state.text = optimizer_result
        Code_exec.Code = optimizer_result
        Logic_errc.error = None  # Reset error
        state.Status.append("Logic_optimized")
    return state

def optimizer(state: State):
    state.Node.append('Optimizer')
    # Additional optimization if needed
    optimized_code = agent.optimizer(
        file_path=Code_exec.file_path,
        Error=Code_exec if Code_exec.error else Logic_errc
    )
    state.text = optimized_code
    Code_exec.Code = optimized_code
    state.Status.append("Code_optimized")
    return state

def generate_test_cases(state: State):
    state.Node.append('Generate_test_cases')
    if Code_exec.file_path:
        tests = agent.generated_the_textcases(Code_exec.file_path)
        state.text = tests
        state.Status.append("Test_cases_generated")
    return state

# Example of connecting the workflow using StateGraph
workflow = StateGraph(State)
workflow.add_node("Preprocessing", preprocessing)
workflow.add_node("Planner", planner)
workflow.add_node("Generate_code", Generate_code)
workflow.add_node("Evaluator", Evaluator)
workflow.add_node("Code_check", code_check)
workflow.add_node("Logic_check", logic_check)
workflow.add_node("Optimizer", optimizer)
workflow.add_node("Generate_test_cases", generate_test_cases)

# Set up the workflow connections
workflow.set_entry_point("Preprocessing")

# Add conditional edges from Planner
workflow.add_conditional_edges(
    "Planner",
    lambda state: planner(state),
    {
        "Generate_code": "Generate_code",
        "Evaluator": "Evaluator",
        "Generate_test_cases": "Generate_test_cases",
        "END": "__end__"
    }
)

# Add conditional edges from Evaluator
workflow.add_conditional_edges(
    "Evaluator",
    lambda state: Evaluator(state),
    {
        "Code_check": "Code_check",
        "Logic_check": "Logic_check",
        "Generate_test_cases": "Generate_test_cases",
        "planner": "Planner"
    }
)

# Connect other nodes
workflow.add_edge("Preprocessing", "Planner")
workflow.add_edge("Generate_code", "Evaluator")
workflow.add_edge("Code_check", "Planner")
workflow.add_edge("Logic_check", "Planner")
workflow.add_edge("Optimizer", "Planner")
workflow.add_edge("Generate_test_cases", "__end__")

# Compile the workflow
app = workflow.compile()
result=app.invoke(State())

