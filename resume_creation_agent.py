#!/usr/bin/env python3

import json
import os
from typing import Dict, List, Callable, Any, Optional
from dotenv import load_dotenv
from datetime import datetime
from file_tools import (
    get_file_line_count, list_dir, search_in_file, read_file_lines, write_file_lines
)

try:
    from langfuse.openai import openai
    from langfuse import observe
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not installed. Install with: pip install openai")



class AgenticLoop:
    """
    A flexible agentic loop that can use tools, follow system prompts, and complete tasks
    """
    
    def __init__(
        self,
        system_prompt: str,
        tools: Dict[str, Callable],
        model: str = "gpt-4o-mini",
        max_iterations: int = 20,
        api_key: Optional[str] = None,
        log_dir: str = "logs"
    ):
        """
        Initialize the agentic loop
        
        Args:
            system_prompt: The system prompt that defines the agent's role and behavior
            tools: Dictionary mapping tool names to callable functions
            model: OpenAI model to use
            max_iterations: Maximum number of iterations before stopping
            api_key: OpenAI API key (if None, loads from .env)
            log_dir: Directory to save logs
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI not installed. Install with: pip install openai")
        
        load_dotenv()
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in .env file")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.system_prompt = system_prompt
        self.tools = tools
        self.model = model
        self.max_iterations = max_iterations
        self.conversation_history = []
        self.iteration_count = 0
        self.log_dir = log_dir
        self.session_log_path = None
        
        # Initialize session log
        self._initialize_session_log()
        
    def _get_tool_schemas(self) -> List[Dict]:
        """Convert tools dictionary to OpenAI function calling schema"""
        schemas = []
        for tool_name, tool_func in self.tools.items():
            # Get function signature and docstring
            import inspect
            sig = inspect.signature(tool_func)
            doc = tool_func.__doc__ or ""
            
            # Build parameter schema
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                param_type = "string"  # default
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_type = "array"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": doc.split('\n')[0] if doc else f"Tool: {tool_name}",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        
        return schemas
    
    def _call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Execute a tool with given arguments"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**arguments)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _format_tool_result(self, tool_name: str, result: Any) -> str:
        """Format tool result for LLM consumption"""
        if isinstance(result, dict) and "error" in result:
            return f"Error calling {tool_name}: {result['error']}"
        
        try:
            return json.dumps(result, indent=2, ensure_ascii=False)
        except:
            return str(result)
    
    @observe(capture_input=True, capture_output=True)
    def run(self, task: str) -> Dict[str, Any]:
        """
        Run the agentic loop to complete a task
        
        Args:
            task: The task description for the agent
        
        Returns:
            Dictionary with 'result', 'iterations', 'conversation_history', and 'final_message'
        """
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

        self.conversation_history.append({
            "role": "user",
            "content": task
        })
        
        self.iteration_count = 0
        
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            
            messages = self.conversation_history.copy()
            tools = self._get_tool_schemas() if self.tools else None
            
            # Make API call
            try:
                if tools:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto"
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages
                    )
            except Exception as e:
                return {
                    "result": None,
                    "error": str(e),
                    "iterations": self.iteration_count,
                    "conversation_history": self.conversation_history
                }
            
            message = response.choices[0].message
            assistant_message = {
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls
            }
            self.conversation_history.append(assistant_message)
            
            # Check if agent wants to use tools
            if message.tool_calls:
                # Execute all tool calls
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except:
                        arguments = {}
                    
                    # Call the tool
                    tool_result = self._call_tool(tool_name, arguments)
                    formatted_result = self._format_tool_result(tool_name, tool_result)
                    
                    # Add tool result to conversation
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": formatted_result
                    }
                    self.conversation_history.append(tool_message)
                
                continue
            
            # If no tool calls and we have content, check if task is complete
            if message.content:
                # Check for completion signals 
                content_lower = message.content.lower()
                if any(signal in content_lower for signal in ["task complete"]) or self.iteration_count >= 2 and not message.tool_calls:
                    print(f"[STATUS] Task completed in {self.iteration_count} iteration(s)")
                    
                    return {
                        "result": message.content,
                        "iterations": self.iteration_count,
                        "conversation_history": self.conversation_history,
                        "final_message": message.content
                    }
            
        
        # Max iterations reached
        final_message = self.conversation_history[-1].get("content", "Max iterations reached")
        print(f"[WARNING] Max iterations ({self.max_iterations}) reached")
        
        return {
            "result": final_message,
            "iterations": self.iteration_count,
            "conversation_history": self.conversation_history,
            "final_message": final_message,
            "warning": "Max iterations reached"
        }
    
    def _initialize_session_log(self):
        """Initialize a new session log file"""
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"agent_session_{timestamp}.json"
        self.session_log_path = os.path.join(self.log_dir, log_filename)
        
        # Create initial log file
        initial_log = {
            "session_start": datetime.now().isoformat(),
            "model": self.model,
            "max_iterations": self.max_iterations,
            "interactions": []
        }
        
        try:
            with open(self.session_log_path, 'w', encoding='utf-8') as f:
                json.dump(initial_log, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"[ERROR] Failed to initialize session log: {e}")
    
    def save_log(self) -> str:
        """
        Append the current conversation to the session log file
        
        Returns:
            Path to the log file
        """
        if not self.session_log_path:
            print("[ERROR] No session log initialized")
            return ""
        
        try:
            # Read existing log
            with open(self.session_log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # Append current interaction
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "iteration_count": self.iteration_count,
                "conversation_history": self.conversation_history
            }
            log_data["interactions"].append(interaction)
            log_data["last_updated"] = datetime.now().isoformat()
            
            # Write back to file
            with open(self.session_log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
            
            return self.session_log_path
        except Exception as e:
            print(f"[ERROR] Failed to save log: {e}")
            return ""


if __name__ == "__main__":
    # Create tools dictionary
    tools = {
        "get_file_line_count": get_file_line_count, 
        "list_dir": list_dir, 
        "search_in_file": search_in_file, 
        "read_file_lines": read_file_lines, 
        "write_file_lines": write_file_lines
    }

    # Define system prompt
    system_prompt = """You are a helpful AI assistant that can use tools to complete tasks. You are currently placed within a working directory containing multiple files, such as:

    - Job description data scraped from LinkedIn
    - Text files with a candidate’s experience and background information
    - LaTeX files containing resume formatting templates

    Your overall goal is to assist the user in their journey to find a job that matches their skills and to help them write or improve their resume.

    Guidelines:

    - Use the available tools at your discretion to achieve the task.
    - Always explain what you are doing and provide clear, actionable results.
    - Plan your approach before executing.
    - When reading file data, summarize the key information relevant to the current task before proceeding.
    - Focus on making small, high-quality improvements rather than broad or unfocused changes.
    - Use the key phrase “task complete” only when the task is fully accomplished or when you need user input to continue.
    - If a question can be answered simply, do so concisely.
    - When working with files, read and process one file at a time.
    - When helping with resumes, follow best practices for clarity, conciseness, and impact in professional writing.
    - When writing files, place them in the "agent_output" folder.
    - When conducting analysis tasks, create a notes file and update it with the state of the task a purtinent information, for example, if you are conducting a study on the user's experience, I want you summarize your notes into the notes file.
    """

    agent = AgenticLoop(
        system_prompt=system_prompt,
        tools=tools,
        model="gpt-4o-mini",
        max_iterations=10
    )

    demo_mode = True
    if not demo_mode:    # Interative Mode
        user_prompt = input("\nEnter instruction (or 'quit' to exit): ")
        
        if user_prompt.lower() in ['quit', 'exit', 'q']:
            print("Exiting...")
            exit()

        result = agent.run(user_prompt)
        
        agent.save_log()

    else:   # Demo mode
        user_prompt = "I would like you to search for the 1 job that best aligns with my experience, and create me a resume for it."

        result = agent.run(user_prompt)
