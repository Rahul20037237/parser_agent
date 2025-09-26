#!/usr/bin/env python3
"""
Parser Agent Workflow with Command Line Interface
Usage: python workflow.py [options]
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv 
from IPython.display import Image

load_dotenv() 

# Add workspace to path
sys.path.append(r'D:\WORKSPACE\agents')

try:
    from paraser_agent import Parser_agent, Code_exe, Logic_err, Prompt
    from logger import log_workflow_step, log_state_transition, log_execution_context, log_execution_summary, logger
except ImportError as e:
    from .paraser_agent import Parser_agent, Code_exe, Logic_err, Prompt
    from .logger import log_workflow_step, log_state_transition, log_execution_context, log_execution_summary, logger

from langgraph.graph import StateGraph
from pydantic import BaseModel
from langsmith import traceable
from typing import List, Optional

# Default paths - can be overridden by command line arguments
DEFAULT_GEN_PATH = Path(r'D:\WORKSPACE\agents\custom_parser\parser')
DEFAULT_DIR_PATH = Path(r'C:\Users\rohith\Downloads\ai-agent-challenge-main\ai-agent-challenge-main\data\icici')
DEFAULT_TEST_DATA = Path(r'D:\WORKSPACE\agents\Testing\test_data\result.csv')

# Global variables that will be set by argparse
GEN_PATH = DEFAULT_GEN_PATH
DIR_PATH = DEFAULT_DIR_PATH
TEST_DATA = DEFAULT_TEST_DATA
MAX_TRIES = 3
VERBOSE = False

# Initialize global objects
agent = None
Code_exec = Code_exe()
Logic_errc = Logic_err()

class State(BaseModel):
    Node: Optional[List[str]] = None
    Status: Optional[List[str]] = None
    Dir_path: Optional[str] = None
    text: Optional[str] = None
    tries: Optional[int] = 0
    next_step: Optional[str] = None

@traceable
@log_workflow_step 
def preprocessing(state: State):
    if VERBOSE:
        print("Executing preprocessing step...")
    file_reader = agent.read_file()
    state.Status = [file_reader.__class__.__name__]
    state.Node = ['preprocessing']
    state.text = next(file_reader)
    if VERBOSE:
        print(f"Text length: {len(state.text) if state.text else 0} characters")
    return state

@traceable
@log_state_transition
def planner(state: State):
    if VERBOSE:
        print(f"Executing planner step... (Try {state.tries + 1}/{MAX_TRIES})")
    
    state.Node.append('planner')
    
    # Check if max tries exceeded
    if state.tries >= MAX_TRIES:
        print(f"Maximum tries ({MAX_TRIES}) exceeded. Ending workflow.")
        state.next_step = 'END'
        return state
    
    state.tries += 1
    
    # Decision logic for next step
    if Code_exec.file_path is None:
        Code_exec.file_path = DIR_PATH
        Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\code_generated.txt')
        Prompt.tags = {'text': state.text, 'Save_path': str(GEN_PATH), 'filename': 'icici_paraser.py'}
        state.next_step = 'Generate_code'
        if VERBOSE:
            print("Next step: Generate_code")
    elif Code_exec.error or Logic_errc.error:
        state.next_step = 'Evaluator'
        if VERBOSE:
            print("Next step: Evaluator (errors detected)")
    else:
        Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\test_case.txt')
        state.next_step = 'Generate_test_cases'
        if VERBOSE:
            print("Next step: Generate_test_cases")
    
    return state

@traceable
@log_workflow_step 
def generate_code(state: State):
    if VERBOSE:
        print("Executing generate_code step...")
    
    state.Node.append('Generate_code')
    code = agent.write_code(**Prompt.tags)
    state.Status.append("Write_code")
    Code_exec.Code = code
    state.text = code
    
    if VERBOSE:
        print(f"Generated code length: {len(code) if code else 0} characters")
    
    return state

@traceable
@log_workflow_step
def evaluator(state: State):
    if VERBOSE:
        print("Executing evaluator step...")
    
    state.Node.append('Evaluator')
    
    # Execute the code and check for errors
    file_name = f"generated_code_icici"
    success, result, file_path = agent.code_executor_and_checker(
        code=Code_exec.Code,
        dir_path=GEN_PATH,
        file_name=file_name
    )   
    Code_exec.file_path = file_path
    Code_exec.output = result.stdout
    Code_exec.error = result.stderr
    
    if VERBOSE:
        print(f"Code execution success: {success}")
        if result.stdout:
            print(f"stdout: {result.stdout[:200]}...")
        if result.stderr:
            print(f"stderr: {result.stderr[:200]}...")
    
    # Check for code execution errors
    if not success and Code_exec.error:
        Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\code_error.txt')
        Prompt.tags = {'code': Code_exec.Code, 'error': Code_exec.error}
        state.Status.append("Code_execution_failed")
        state.next_step = 'Code_check'
        return state
    else:
        Code_exec.error = None
    
    # If code execution succeeded, check logic
    if success and Code_exec.file_path:
        generated_csv = GEN_PATH / "output.csv" 
        original_csv = TEST_DATA
        
        logic_success = agent.logic_check(original_csv, generated_csv)
        
        if VERBOSE:
            print(f"Logic check success: {logic_success}")
        
        if not logic_success and Logic_errc.error:
            state.Status.append("Logic_check_failed")
            Prompt.instruct = agent.load_prompt(r'D:\WORKSPACE\agents\prompt\logic_error.txt')
            Prompt.tags = {'code': Logic_errc.Code, 'error': Logic_errc.error}
            state.next_step = 'Logic_check'
            return state
        else:
            Logic_errc.error = None
    
    # If both code execution and logic check passed, go back to planner
    state.Status.append("Evaluation_passed")
    state.next_step = 'Planner'
    return state

@traceable
@log_workflow_step 
def code_check(state: State):
    if VERBOSE:
        print("Executing code_check step...")
    
    state.Node.append('Code_check')
    if Code_exec.error:
        # Fix the code using the optimizer
        fixed_code = agent.optimizer(
            file_path=Code_exec.file_path,
            Error=Code_exec
        )
        state.text = fixed_code
        Code_exec.Code = fixed_code
        Code_exec.error = None  # Reset error
        state.Status.append("Code_fixed")
        
        if VERBOSE:
            print(f"Code fixed, new length: {len(fixed_code) if fixed_code else 0} characters")
    
    return state

@traceable
@log_workflow_step 
def logic_check(state: State):
    if VERBOSE:
        print("Executing logic_check step...")
    
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
        
        if VERBOSE:
            print(f"Logic optimized, new length: {len(optimizer_result) if optimizer_result else 0} characters")
    
    return state

@traceable
@log_workflow_step 
def generate_test_cases(state: State):
    if VERBOSE:
        print("Executing generate_test_cases step...")
    
    state.Node.append('Generate_test_cases')
    if Code_exec.file_path:
        tests = agent.generated_the_textcases(Code_exec.file_path, str('genertaed_icici'))
        state.text = tests
        state.Status.append("Test_cases_generated")
        
        if VERBOSE:
            print(f"Generated test cases length: {len(tests) if tests else 0} characters")
    
    return state

def create_workflow():
    """Create and configure the workflow graph."""
    # Create the workflow using StateGraph
    workflow = StateGraph(State)

    # Add all nodes
    workflow.add_node("Preprocessing", preprocessing)
    workflow.add_node("Planner", planner)
    workflow.add_node("Generate_code", generate_code)
    workflow.add_node("Evaluator", evaluator)
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
            "Evaluator": "Evaluator",
            "Generate_test_cases": "Generate_test_cases",
            "END": "__end__"
        }
    )

    # Add conditional edges from Evaluator
    workflow.add_conditional_edges(
        "Evaluator",
        lambda state: state.next_step,
        { 
            "Code_check": "Code_check",
            "Logic_check": "Logic_check",
            "Planner": "Planner"
        }
    )

    # Connect other nodes
    workflow.add_edge("Preprocessing", "Planner")
    workflow.add_edge("Generate_code", "Evaluator")
    workflow.add_edge("Code_check", "Planner")
    workflow.add_edge("Logic_check", "Planner")
    workflow.add_edge("Generate_test_cases", "__end__")

    return workflow.compile()

def save_workflow_diagram(output_path="langgraph_workflow.png"):
    """Generate and save workflow diagram."""
    try:
        app = create_workflow()
        mermaid_png_data = app.get_graph().draw_mermaid_png()
        with open(output_path, 'wb') as f:
            f.write(mermaid_png_data)
        print(f"Workflow diagram saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving workflow diagram: {e}")
        return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Execute Parser Agent Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run with default settings
  %(prog)s --verbose                          # Run with detailed output
  %(prog)s --dir-path "C:/my/data"           # Custom input directory
  %(prog)s --max-tries 5                     # Allow up to 5 tries
  %(prog)s --no-diagram --quiet              # Skip diagram, minimal output
  %(prog)s --gen-path "./output" --verbose   # Custom output path with details
        """
    )
    
    # Path arguments
    parser.add_argument(
        '--dir-path', 
        type=str, 
        default=str(DEFAULT_DIR_PATH), 
        help=f'Directory path for input data (default: {DEFAULT_DIR_PATH})'
    )
    
    parser.add_argument(
        '--gen-path', 
        type=str, 
        default=str(DEFAULT_GEN_PATH),
        help=f'Directory path for generated files (default: {DEFAULT_GEN_PATH})'
    )
    
    parser.add_argument(
        '--test-data', 
        type=str, 
        default=str(DEFAULT_TEST_DATA),
        help=f'Path to test data CSV file (default: {DEFAULT_TEST_DATA})'
    )
    
    # Workflow control arguments
    parser.add_argument(
        '--max-tries', 
        type=int, 
        default=3,
        help='Maximum number of tries for the workflow (default: 3)'
    )
    
    # Output control arguments
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose output with detailed step information'
    )
    
    parser.add_argument(
        '--quiet', '-q', 
        action='store_true',
        help='Suppress non-essential output'
    )
    
    parser.add_argument(
        '--no-diagram', 
        action='store_true',
        help='Skip generating workflow diagram'
    )
    
    parser.add_argument(
        '--diagram-path', 
        type=str, 
        default='langgraph_workflow.png',
        help='Path for saving workflow diagram (default: langgraph_workflow.png)'
    )
    
    # Validation arguments
    parser.add_argument(
        '--validate-paths', 
        action='store_true',
        help='Validate that all specified paths exist before running'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show configuration and exit without running workflow'
    )
    
    return parser.parse_args()

def validate_paths(args):
    """Validate that required paths exist."""
    errors = []
    
    # Check if input directory exists
    if not Path(args.dir_path).exists():
        errors.append(f"Input directory does not exist: {args.dir_path}")
    
    # Check if test data file exists
    if not Path(args.test_data).exists():
        errors.append(f"Test data file does not exist: {args.test_data}")
    
    # Check if generation path parent directory exists
    gen_path_parent = Path(args.gen_path).parent
    if not gen_path_parent.exists():
        errors.append(f"Generation path parent directory does not exist: {gen_path_parent}")
    
    if errors:
        print("Path validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

def main():
    """Main function to parse arguments and execute workflow."""
    global GEN_PATH, DIR_PATH, TEST_DATA, MAX_TRIES, VERBOSE, agent
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle quiet mode
    if args.quiet and args.verbose:
        print("Warning: --quiet and --verbose are mutually exclusive. Using --verbose.")
    
    # Set global variables
    DIR_PATH = Path(args.dir_path)
    GEN_PATH = Path(args.gen_path)
    TEST_DATA = Path(args.test_data)
    MAX_TRIES = args.max_tries
    VERBOSE = args.verbose and not args.quiet
    
    # Create generation directory if it doesn't exist
    GEN_PATH.mkdir(parents=True, exist_ok=True)
    
    # Validate paths if requested
    if args.validate_paths:
        if not validate_paths(args):
            return 1
    
    # Initialize agent with specified directory
    try:
        agent = Parser_agent(DIR_PATH)
    except Exception as e:
        print(f"Error initializing Parser_agent: {e}")
        return 1
    
    # Show configuration
    if not args.quiet:
        print("Parser Agent Workflow Configuration:")
        print(f"  Input Directory: {DIR_PATH}")
        print(f"  Generation Path: {GEN_PATH}")
        print(f"  Test Data Path: {TEST_DATA}")
        print(f"  Max Tries: {MAX_TRIES}")
        print(f"  Verbose Mode: {VERBOSE}")
        print(f"  Generate Diagram: {not args.no_diagram}")
        print()
    
    # Dry run mode
    if args.dry_run:
        print("Dry run mode - configuration shown above. Exiting.")
        return 0
    
    # Generate workflow diagram unless skipped
    if not args.no_diagram:
        if not args.quiet:
            print("Generating workflow diagram...")
        save_workflow_diagram(args.diagram_path)
        if not args.quiet:
            print()
    
    # Create and execute workflow
    try:
        if not args.quiet:
            print("Starting workflow execution...")
        
        app = create_workflow()
        initial_state = State(tries=0)
        
        result = app.invoke(initial_state)
        
        if not args.quiet:
            print("Workflow completed successfully!")
            print()
        
        # Show results
        if VERBOSE:
            print("Detailed Results:")
            print(f"  Nodes Visited: {' -> '.join(result.Node) if result.Node else 'None'}")
            print(f"  Status History: {result.Status}")
            print(f"  Total Tries: {result.tries}")
            print(f"  Final Next Step: {result.next_step}")
            if result.text:
                print(f"  Final Text Length: {len(result.text)} characters")
        elif not args.quiet:
            print("Summary:")
            print(f"  Completed in {result.tries} tries")
            print(f"  Final Status: {result.Status[-1] if result.Status else 'Unknown'}")
            print(f"  Nodes Visited: {len(result.Node) if result.Node else 0}")
        
        return 0
        
    except Exception as e:
        print(f"Workflow execution error: {e}")
        if VERBOSE:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)