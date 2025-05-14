from mcp.server.fastmcp import FastMCP
import os
import pathlib

mcp = FastMCP(name="file_server")

# 设置允许访问的基础目录(限制在data目录下)
BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB文件大小限制


@mcp.tool()
def read_file(file_path: str) -> str:
    """
    安全读取文件内容
    Args:
        file_path: 相对于项目根目录的文件路径
    Returns:
        文件内容字符串
    """
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return {"error": f"File size exceeds limit of {MAX_FILE_SIZE} bytes"}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return {
                "content": f.read(),
                "file_size": file_size,
                "encoding": "utf-8"
            }
    except FileNotFoundError:
        return {"error": "File not found"}
    except PermissionError:
        return {"error": "Permission denied"}
    except UnicodeDecodeError:
        return {"error": "File encoding not supported"}
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

@mcp.tool()
def write_file(file_path: str, content: str) -> dict:
    """
    安全写入文件内容
    Args:
        file_path: 相对于项目根目录的文件路径
        content: 要写入的内容
    Returns:
        操作结果状态
    """
    
    try:
        # 检查内容大小
        if len(content.encode('utf-8')) > MAX_FILE_SIZE:
            return {"error": f"Content size exceeds limit of {MAX_FILE_SIZE} bytes"}
            
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "status": "success", 
            "file_path": file_path,
            "file_size": len(content.encode('utf-8'))
        }
    except PermissionError:
        return {"error": "Permission denied"}
    except IsADirectoryError:
        return {"error": "Path is a directory"}
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport="stdio")