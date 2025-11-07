from typing import Dict, List
import os

def search_in_file(filepath: str, query: str) -> Dict:
    """
    Search for a query string within a file's contents
    
    Args:
        filepath: Path to the file to search
        query: The search query (case-insensitive)
    
    Returns:
        Dictionary with matching lines and their line numbers
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        matches = []
        for i, line in enumerate(lines, 1):
            if query.lower() in line.lower():
                matches.append({
                    "line_number": i,
                    "content": line.strip()
                })
        
        return {
            "filepath": filepath,
            "query": query,
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        return {"error": str(e)}

def list_dir(path: str) -> Dict:
    """List directory contents with file type information"""
    try:
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            item_info = {
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "extension": os.path.splitext(item)[1] if os.path.isfile(item_path) else None
            }
            items.append(item_info)
        
        return {
            "path": path,
            "items": items,
            "count": len(items)
        }
    except Exception as e:
        return {"error": str(e)}

def get_file_line_count(filepath: str) -> Dict:
    """
    Get the total number of lines in a file
    
    Args:
        filepath: Path to the file
    
    Returns:
        Dictionary with filepath and line_count
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        
        return {
            "filepath": filepath,
            "line_count": line_count
        }
    except Exception as e:
        return {"error": str(e)}

def read_file_lines(filepath: str, start_line: int, end_line: int) -> Dict:
    """
    Read specific lines from a file (0-indexed, inclusive)
    
    Args:
        filepath: Path to the file
        start_line: Starting line number (0-indexed, inclusive)
        end_line: Ending line number (0-indexed, inclusive)
    
    Returns:
        Dictionary with filepath, start_line, end_line, and content (list of lines)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # Validate line numbers
        if start_line < 0:
            return {"error": f"start_line must be >= 0, got {start_line}"}
        if end_line < start_line:
            return {"error": f"end_line ({end_line}) must be >= start_line ({start_line})"}
        if start_line >= total_lines:
            return {"error": f"start_line ({start_line}) exceeds or equals file length ({total_lines})"}
        
        # Adjust end_line if it exceeds file length
        end_line = min(end_line, total_lines - 1)
        
        # Extract requested lines (0-indexed, inclusive)
        # Python slice is exclusive on the stop, so +1 to include end_line
        selected_lines = lines[start_line:end_line + 1]
        
        return {
            "filepath": filepath,
            "start_line": start_line,
            "end_line": end_line,
            "total_lines": total_lines,
            "content": [line.rstrip('\n') for line in selected_lines],
            "line_count": len(selected_lines)
        }
    except Exception as e:
        return {"error": str(e)}

def write_file_lines(filepath: str, start_line: int, end_line: int, new_content: List[str]) -> Dict:
    """
    Replace a range of lines in a file with new content (1-indexed, inclusive)
    
    Args:
        filepath: Path to the file
        start_line: Starting line number (1-indexed, inclusive)
        end_line: Ending line number (1-indexed, inclusive)
        new_content: List of strings to replace the lines with (each string becomes a line)
    
    Returns:
        Dictionary with status and information about the replacement
    """
    try:
        # Read existing file
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # Validate line numbers
        if start_line < 1:
            return {"error": f"start_line must be >= 1, got {start_line}"}
        if end_line < start_line:
            return {"error": f"end_line ({end_line}) must be >= start_line ({start_line})"}
        if start_line > total_lines:
            return {"error": f"start_line ({start_line}) exceeds file length ({total_lines})"}
        
        # Adjust end_line if it exceeds file length
        end_line = min(end_line, total_lines)
        
        # Replace the lines
        # Convert new_content to list of lines with newlines
        new_lines = [line + '\n' if not line.endswith('\n') else line for line in new_content]
        
        # Replace the range (convert to 0-indexed)
        lines[start_line - 1:end_line] = new_lines
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return {
            "status": "success",
            "filepath": filepath,
            "start_line": start_line,
            "end_line": end_line,
            "old_line_count": end_line - start_line + 1,
            "new_line_count": len(new_content),
            "total_lines": len(lines)
        }
    except Exception as e:
        return {"error": str(e)}
