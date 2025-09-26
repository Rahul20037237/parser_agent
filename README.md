# Parser Agent Workflow

A sophisticated AI-powered workflow system for automated code generation, testing, and optimization using LangGraph and LangSmith. This tool processes input data, generates parsing code, evaluates performance, and iteratively improves the solution.

## 🚀 Features

- **Automated Code Generation**: AI-powered parser code creation from input specifications
- **Self-Healing Workflow**: Automatic error detection and correction
- **Logic Validation**: Comprehensive output validation against test data
- **Test Case Generation**: Automated test suite creation
- **Visual Workflow**: Mermaid diagram generation for process visualization
- **Command Line Interface**: Full CLI support with extensive configuration options
- **Comprehensive Logging**: Detailed workflow step and state transition logging

## 📋 Prerequisites

- Python 3.8+
- Required Python packages (see [Installation](#installation))
- LangSmith API key (optional for tracing)
- Directory structure as specified in configuration

## 🛠 Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd parser-agent-workflow
```

2. **Install required packages:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
# Create .env file
echo "LANGSMITH_API_KEY=your_api_key_here" > .env
```

4. **Verify installation:**
```bash
python workflow.py --help
```

## 📁 Project Structure

```
parser-agent-workflow/
├── workflow.py                 # Main workflow script
├── paraser_agent.py           # Parser agent implementation
├── logger.py                  # Logging utilities
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── README.md                  # This file
├── prompt/                    # Prompt templates
│   ├── code_generated.txt
│   ├── code_error.txt
│   ├── logic_error.txt
│   └── test_case.txt
├── custom_parser/parser/      # Generated code output
└── Testing/test_data/         # Test data files
    └── result.csv
```

## 🎯 Usage

### Basic Usage

```bash
# Run with default settings
python workflow.py

# Run with verbose output
python workflow.py --verbose

# Run quietly (minimal output)
python workflow.py --quiet
```

### Path Configuration

```bash
# Specify custom input directory
python workflow.py --dir-path "/path/to/input/data"

# Specify custom output directory
python workflow.py --gen-path "/path/to/output"

# Specify custom test data
python workflow.py --test-data "/path/to/test.csv"
```

### Workflow Control

```bash
# Set maximum tries
python workflow.py --max-tries 5

# Validate paths before running
python workflow.py --validate-paths

# Dry run (show config without executing)
python workflow.py --dry-run
```

### Output Control

```bash
# Skip diagram generation
python workflow.py --no-diagram

# Custom diagram path
python workflow.py --diagram-path "my_workflow.png"

# Combine options
python workflow.py --verbose --max-tries 3 --no-diagram
```

## 📊 Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--dir-path` | | Input directory path | `C:\Users\rohith\Downloads\...` |
| `--gen-path` | | Generated files output path | `D:\WORKSPACE\agents\...` |
| `--test-data` | | Test data CSV file path | `D:\WORKSPACE\agents\Testing\...` |
| `--max-tries` | | Maximum workflow attempts | `3` |
| `--verbose` | `-v` | Enable detailed output | `False` |
| `--quiet` | `-q` | Suppress non-essential output | `False` |
| `--no-diagram` | | Skip workflow diagram generation | `False` |
| `--diagram-path` | | Custom diagram save path | `langgraph_workflow.png` |
| `--validate-paths` | | Validate paths before execution | `False` |
| `--dry-run` | | Show configuration and exit | `False` |
| `--help` | `-h` | Show help message | |

## 🔄 Workflow Steps

The workflow consists of the following key steps:

1. **Preprocessing** 📝
   - Reads input files from the specified directory
   - Initializes workflow state

2. **Planner** 🎯
   - Determines next action based on current state
   - Manages retry logic and workflow termination

3. **Generate Code** ⚙️
   - Creates parser code using AI agents
   - Saves generated code to output directory

4. **Evaluator** 🔍
   - Executes generated code
   - Validates logic against test data
   - Identifies errors for correction

5. **Code Check** 🐛
   - Fixes code execution errors
   - Uses optimizer to improve code quality

6. **Logic Check** 🧠
   - Corrects logical errors in output
   - Optimizes algorithm performance

7. **Generate Test Cases** 🧪
   - Creates comprehensive test suite
   - Validates final solution

## 📈 Output Examples

### Normal Mode
```
Parser Agent Workflow Configuration:
  Input Directory: C:\Users\rohith\Downloads\ai-agent-challenge-main\data\icici
  Generation Path: D:\WORKSPACE\agents\custom_parser\parser
  Test Data Path: D:\WORKSPACE\agents\Testing\test_data\result.csv
  Max Tries: 3
  Verbose Mode: False
  Generate Diagram: True

Generating workflow diagram...
Workflow diagram saved to: langgraph_workflow.png

Starting workflow execution...
Workflow completed successfully!

Summary:
  Completed in 2 tries
  Final Status: Test_cases_generated
  Nodes Visited: 6
```

### Verbose Mode
```
Executing preprocessing step...
Text length: 1547 characters
Executing planner step... (Try 1/3)
Next step: Generate_code
Executing generate_code step...
Generated code length: 2341 characters
Executing evaluator step...
Code execution success: True
Logic check success: True
...
Detailed Results:
  Nodes Visited: preprocessing -> planner -> Generate_code -> Evaluator -> planner -> Generate_test_cases
  Status History: ['FileReader', 'Write_code', 'Evaluation_passed', 'Test_cases_generated']
  Total Tries: 2
  Final Next Step: None
  Final Text Length: 892 characters
```

## 🐛 Troubleshooting

### Common Issues

**Path not found errors:**
```bash
# Validate paths before running
python workflow.py --validate-paths
```

**Import errors:**
- Ensure all required packages are installed
- Check Python path configuration
- Verify workspace directory structure

**Workflow timeout/max tries exceeded:**
```bash
# Increase max tries
python workflow.py --max-tries 10
```

**Debug mode:**
```bash
# Run with maximum verbosity
python workflow.py --verbose --validate-paths
```

### Log Files

The workflow generates detailed logs for debugging:
- Workflow step logs
- State transition logs  
- Execution context logs
- Execution summary logs

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# LangSmith configuration (optional)
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_PROJECT=parser-agent-workflow

# Custom paths (optional)
WORKSPACE_PATH=D:\WORKSPACE\agents
INPUT_DATA_PATH=C:\path\to\input
OUTPUT_PATH=C:\path\to\output
```

### Default Paths

Update the default paths in `workflow.py`:

```python
DEFAULT_GEN_PATH = Path(r'your\custom\output\path')
DEFAULT_DIR_PATH = Path(r'your\custom\input\path') 
DEFAULT_TEST_DATA = Path(r'your\custom\test\data.csv')
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- LangGraph for workflow orchestration
- LangSmith for tracing and monitoring
- The open-source community for inspiration and tools

---

**Made with ❤️ by RAHUL A
