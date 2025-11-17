from typing import Dict, List, Callable, Any, Optional
from dotenv import load_dotenv
import os

import json
from datetime import datetime

try:
    from langfuse.openai import openai
    from langfuse import observe
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not installed. Install with: pip install openai")

class Agent:
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
    ):
        """
        Initialize the agentic loop
        
        Args:
            system_prompt: The system prompt that defines the agent's role and behavior
            tools: Dictionary mapping tool names to callable functions
            model: OpenAI model to use
            max_iterations: Maximum number of iterations before stopping
            api_key: OpenAI API key (if None, loads from .env)
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
        self.session_log_path = None
        
    def _get_tool_schemas(self) -> List[Dict]:
        """Convert tools dictionary to OpenAI function calling schema"""
        schemas = []
        for tool_name, tool_func in self.tools.items():
            # Get function signature and docstring
            import inspect
            sig = inspect.signature(tool_func)
            doc = inspect.getdoc(tool_func) or ""
            
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
                    "description": doc if doc else f"Tool: {tool_name}",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        
        return schemas
    
    def _call_tool(self, tool_name: str, arguments: Dict) -> Dict[str, Any]:
        """Execute a tool with given arguments
        
        Returns a standard structure:
        - Success: {"success": True, "data": <result>}
        - Error: {"success": False, "error": "<error message>", "tool_name": "<name>", "arguments": {...}}
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "tool_name": tool_name,
                "arguments": arguments
            }
        
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**arguments)
            
            # Check function return type annotation to determine if string is data or error
            import inspect
            from typing import get_origin, get_args
            
            sig = inspect.signature(tool_func)
            return_annotation = sig.return_annotation
            
            # Determine if this is an Optional type (Union[T, None])
            is_optional = False
            if return_annotation != inspect.Parameter.empty:
                # Check if it's a plain str type (not Optional)
                if return_annotation == str:
                    # Pure str type means string is data, not error
                    return {"success": True, "data": result}
                
                origin = get_origin(return_annotation)
                args = get_args(return_annotation) if origin else ()
                
                # Check if it's Optional (Union with None)
                # get_origin(Optional[str]) returns typing.Union
                if origin is not None:
                    # Check if it's a Union type and contains None
                    origin_str = str(origin)
                    if 'Union' in origin_str or (hasattr(origin, '__name__') and origin.__name__ == 'Union'):
                        is_optional = type(None) in args
            
            # If Optional type: None = success, str = error
            # Otherwise: None = success, string starting with "Error:" = error, else = data
            if result is None:
                return {"success": True, "data": None}
            elif isinstance(result, str):
                if is_optional:
                    # For Optional[str], any string is an error
                    return {
                        "success": False,
                        "error": result,
                        "tool_name": tool_name,
                        "arguments": arguments
                    }
                elif result.startswith("Error:"):
                    # For other types, only strings starting with "Error:" are errors
                    return {
                        "success": False,
                        "error": result,
                        "tool_name": tool_name,
                        "arguments": arguments
                    }
                else:
                    # String data (e.g., from view_current_resume_contents or save)
                    return {"success": True, "data": result}
            else:
                # Any other result is treated as successful data
                return {"success": True, "data": result}
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "arguments": arguments
            }
    
    def _format_tool_result(self, tool_name: str, result: Any) -> str:
        """Format tool result for LLM consumption
        
        Expects result to be in standard format:
        - {"success": True, "data": <any>} for success
        - {"success": False, "error": "<message>", "tool_name": "<name>", "arguments": {...}} for errors
        """

        if isinstance(result, dict) and "success" in result:
            if result["success"]:
                # Success case - format the data
                data = result.get("data")
                if data is None:
                    return "Success: Operation completed successfully."
                try:
                    data_str = json.dumps(data, indent=2, ensure_ascii=False)
                    return f"Success: {data_str}"
                except:
                    return f"Success: {str(data)}"
            else:
                # Error case - include arguments context
                error_msg = result.get("error", "Unknown error")
                arguments = result.get("arguments", {})
                tool_name_used = result.get("tool_name", tool_name)
                args_str = json.dumps(arguments, indent=2, ensure_ascii=False)
                return f"Error calling {tool_name_used} with arguments:\n{args_str}\n\nError: {error_msg}"
        
        # Fallback for non-standard results
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
    