import logging
import functools
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import sys

# Configure logging
def setup_logger(log_file="workflow.log", log_level=logging.INFO):
    """
    Setup logger for the workflow
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file).parent
    log_path.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Also log to console
        ]
    )
    
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_logger("logs/langgraph_workflow.log")

def log_workflow_step(func):
    """
    Decorator to log workflow step execution
    """
    @functools.wraps(func)
    def wrapper(state, *args, **kwargs):
        step_name = func.__name__
        
        # Log entry
        logger.info(f" STARTING: {step_name}")
        logger.info(f" INPUT STATE - Node: {getattr(state, 'Node', [])}, Status: {getattr(state, 'Status', [])}, Tries: {getattr(state, 'tries', 0)}")
        
        start_time = datetime.now()
        
        try:
            # Execute the function
            result = func(state, *args, **kwargs)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log success
            logger.info(f"COMPLETED: {step_name} (took {execution_time:.2f}s)")
            if hasattr(result, 'Node'):
                logger.info(f"OUTPUT STATE - Node: {result.Node}, Status: {result.Status}, Next: {getattr(result, 'next_step', 'N/A')}")
            else:
                logger.info(f" OUTPUT: {result}")
            
            return result
            
        except Exception as e:
            # Calculate execution time even for errors
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log error
            logger.error(f"ERROR in {step_name} (after {execution_time:.2f}s): {str(e)}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            
            # Re-raise the exception
            raise
    
    return wrapper

def log_state_transition(func):
    """
    Decorator specifically for state transitions and decisions
    """
    @functools.wraps(func)
    def wrapper(state, *args, **kwargs):
        step_name = func.__name__
        
        # Log the decision making process
        logger.info(f"DECISION POINT: {step_name}")
        
        # Log current state for decision making
        if hasattr(state, 'tries'):
            logger.info(f"Current tries: {state.tries}")
        if hasattr(state, 'next_step'):
            logger.info(f"Previous next_step: {state.next_step}")
        
        result = func(state, *args, **kwargs)
        
        # Log the decision made
        if hasattr(result, 'next_step'):
            logger.info(f"DECISION: Next step will be '{result.next_step}'")
        if isinstance(result, str):
            logger.info(f"DECISION: Returning '{result}'")
        
        return result
    
    return wrapper

def log_execution_context():
    """
    Log the execution context and environment
    """
    logger.info("=" * 80)
    logger.info("WORKFLOW EXECUTION STARTED")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")
    logger.info("=" * 80)

def log_execution_summary(state):
    """
    Log execution summary
    """
    logger.info("=" * 80)
    logger.info("WORKFLOW EXECUTION SUMMARY")
    if hasattr(state, 'Node') and state.Node:
        logger.info(f" Nodes executed: {' -> '.join(state.Node)}")
    if hasattr(state, 'Status') and state.Status:
        logger.info(f"Status history: {' -> '.join(state.Status)}")
    if hasattr(state, 'tries'):
        logger.info(f"Total tries: {state.tries}")
    logger.info("=" * 80)
