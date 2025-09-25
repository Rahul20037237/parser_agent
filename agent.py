from dotenv import load_dotenv 
from IPython.display import Image

load_dotenv() 

import sys
sys.path.append(r'D:\WORKSPACE\agents')

try:
    from paraser_agent import Parser_agent, Code_exe, Logic_err, Prompt
except ImportError as e:
    from .paraser_agent import Parser_agent, Code_exe, Logic_err, Prompt
from pathlib import Path
from langgraph.graph import StateGraph
from pydantic import BaseModel
from langsmith import traceable
from typing import List, Optional

GEN_PATH = Path(r'D:\WORKSPACE\agents\custom_parser\parser')
DIR_PATH = Path(r'C:\Users\rohith\Downloads\ai-agent-challenge-main\ai-agent-challenge-main\data\icici')
TEST_DATA = Path(r'D:\WORKSPACE\agents\Testing\test_data\result.csv')

agent=Parser_agent(DIR_PATH)
Code_exec=Code_exe()
Logic_errc=Logic_err()

class State(BaseModel):
    Node: Optional[List[str]] = None
    Status: Optional[List[str]] = None
    Dir_path: Optional[str] = None
    text: Optional[str] = None
    tries: Optional[int] = 0
    next_step: Optional[str] = None

@traceable
def preprocessing(state: State):
    file_reader = agent.read_file()
    state.Status = [file_reader.__class__.__name__]
    state.Node = ['preprocessing']
    state.text = next(file_reader)
    return state

@traceable
def planner(state: State):
    state.Node.append('planner')
    
    # Check if max tries exceeded
    if state.tries > 3:
        state.next_step = 'END'
        return state
    
    state.tries += 1
    
    # Decision logic for next step
    if Code_exec.file_path is None:
        Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\code_generated.txt')
        Prompt.tags={'text':state.text,'Save_path':str(GEN_PATH),'filename':'icici_paraser.py'}
        state.next_step = 'Generate_code'
    elif Code_exec.error:
        Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\code_error.txt')
        Prompt.tags={'code':Code_exec.Code,'error':Code_exec.error}
        state.next_step = 'Code_check'
    elif Logic_errc.error:
        Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\logic_error.txt')
        Prompt.tags={'code':Logic_errc.Code,'error':Logic_errc.error}
        state.next_step = 'Logic_check'
    else:
        Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\test_case.txt')
        state.next_step = 'Generate_test_cases'
    
    return state

@traceable
def Generate_code(state: State):
    state.Node.append('Generate_code')
    code = agent.write_code(**Prompt.tags)
    state.Status.append("Write_code")
    Code_exec.Code = code
    state.text = code
    return state

@traceable
def Evaluator(state: State):
    state.Node.append('Evaluator')
    
    # Execute the code and check for errors
    file_name = f"generated_code_{state.tries}"
    success = agent.code_executor_and_checker(
        code=Code_exec.Code,
        dir_path=GEN_PATH,
        file_name=file_name
    )
    
    # Check for code execution errors
    if not success and Code_exec.error:
        state.Status.append("Code_execution_failed")
        state.next_step = 'Code_check'
        return state
    
    # If code execution succeeded, check logic
    if success and Code_exec.file_path:
        generated_csv = GEN_PATH / "output.csv" 
        original_csv = TEST_DATA
        
        logic_success = agent.logic_check(original_csv, generated_csv)
        
        if not logic_success and Logic_errc.error:
            state.Status.append("Logic_check_failed")
            state.next_step = 'Logic_check'
            return state
    
    # If both code execution and logic check passed, go back to planner
    state.Status.append("Evaluation_passed")
    state.next_step = 'Planner'
    return state

@traceable
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

@traceable
def logic_check(state: State):
    state.Node.append('Logic_check')
    if Logic_errc.error:
        # Optimize the logic using the optimizer
        optimizer_result = agent.optimizer(
            file_path=Code_exec.file_path,
            Error=Logic_errc.error
        )
        state.text = optimizer_result
        Code_exec.Code = optimizer_result
        Logic_errc.error = None  # Reset error
        state.Status.append("Logic_optimized")
    return state

@traceable
def generate_test_cases(state: State):
    state.Node.append('Generate_test_cases')
    if Code_exec.file_path:
        tests = agent.generated_the_textcases(Code_exec.file_path)
        state.text = tests
        state.Status.append("Test_cases_generated")
    return state

# Create the workflow using StateGraph
workflow = StateGraph(State)

# Add all nodes
workflow.add_node("Preprocessing", preprocessing)
workflow.add_node("Planner", planner)
workflow.add_node("Generate_code", Generate_code)
workflow.add_node("Evaluator", Evaluator)
workflow.add_node("Code_check", code_check)
workflow.add_node("Logic_check", logic_check)
workflow.add_node("Generate_test_cases", generate_test_cases)

# Set up the workflow connections
workflow.set_entry_point("Preprocessing")

# Add conditional edges from Planner
workflow.add_conditional_edges(
    "Planner",
    lambda state: state.next_step,
    {
        "Generate_code": "Generate_code",
        "Code_check": "Code_check",
        "Logic_check": "Logic_check", 
        "Generate_test_cases": "Generate_test_cases",
        "END": "__end__"
    }
)

# Add conditional edges from Evaluator - FIXED
workflow.add_conditional_edges(
    "Evaluator",
    lambda state: state.next_step,
    { 
        "Code_check": "Code_check",
        "Logic_check": "Logic_check",
        "Planner": "Planner"  # Added this missing mapping
    }
)

# Connect other nodes
workflow.add_edge("Preprocessing", "Planner")
workflow.add_edge("Generate_code", "Evaluator")
workflow.add_edge("Code_check", "Planner")
workflow.add_edge("Logic_check", "Planner")
workflow.add_edge("Generate_test_cases", "__end__")  # End after generating test cases

# Compile the workflow
app = workflow.compile()

# Visualize and save the workflow
# def save_workflow_diagram():
#     image_path = "langgraph_workflow.png"
#     try:
#         mermaid_png_data = app.get_graph().draw_mermaid_png()
#         with open(image_path, 'wb') as f:
#             f.write(mermaid_png_data)
#         print(f"Workflow diagram saved to: {image_path}")
#         return Image(data=mermaid_png_data)
#     except Exception as e:
#         print(f"Error saving workflow diagram: {e}")
#         return None

# # Save and display the workflow diagram
# workflow_image = save_workflow_diagram()
# if workflow_image:
#     display(workflow_image)

# Execute the workflow
try:
    print("Starting workflow execution...")
    result = app.invoke(State())
    print("Workflow completed successfully!")
    print(f"Final state: {result}")
except Exception as e:
    print(f"Workflow execution error: {e}")
    import traceback
    traceback.print_exc()