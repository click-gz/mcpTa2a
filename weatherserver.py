from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import requests
import os
from datetime import datetime, timedelta, timezone

# 创建MCP服务器实例
mcp = FastMCP(
    name="天气服务",
    description="获取指定位置的当前天气信息",
    version="1.0.0"
)

# 定义数据模型（中文）
class 天气信息(BaseModel):
    位置: str = Field(..., description="地理位置")
    坐标: str = Field(..., description="经纬度坐标")
    时间: str = Field(..., description="数据时间")
    天气状况: str = Field(..., description="天气状况描述")
    温度: str = Field(..., description="温度（摄氏度）")
    体感温度: str = Field(..., description="体感温度（摄氏度）")
    湿度: str = Field(..., description="湿度百分比")
    风速: str = Field(..., description="风速（米/秒）")
    风向: str = Field(..., description="风向（角度）")
    气压: str = Field(..., description="气压（hPa）")
    云量: str = Field(..., description="云层覆盖率")
    降雨量: Optional[str] = Field(None, description="降雨量（毫米）")

# 天气状况英文转中文映射
CONDITION_MAPPING = {
    "clear sky": "晴朗",
    "few clouds": "少云",
    "scattered clouds": "多云",
    "broken clouds": "阴天",
    "shower rain": "阵雨",
    "rain": "雨",
    "thunderstorm": "雷暴",
    "snow": "雪",
    "mist": "薄雾",
    "haze": "霾",
    "fog": "雾"
}

# 获取API密钥
def get_api_key(provided_key: Optional[str] = None) -> str:
    if provided_key:
        return provided_key
    
    env_key = os.environ.get("OPENWEATHER_API_KEY")
    if env_key:
        return env_key
    
    raise ValueError("未提供API密钥，且环境变量中未找到OPENWEATHER_API_KEY")

# 获取天气信息的核心函数
def fetch_weather(location: str, api_key: Optional[str] = None, timezone_offset: float = 0) -> Dict[str, Any]:
    try:
        # 获取API密钥
        key = get_api_key(api_key)
        
        # 获取地理位置信息和天气数据
        geocode_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={key}&units=metric"
        response = requests.get(geocode_url)
        response.raise_for_status()
        data = response.json()
        
        # 转换时间戳为本地时间
        tz = timezone(timedelta(hours=timezone_offset))
        local_time = datetime.fromtimestamp(data['dt'], tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # 获取中文天气状况
        condition_en = data['weather'][0]['description']
        condition_cn = CONDITION_MAPPING.get(condition_en, condition_en)
        
        # 构建返回数据（中文）
        weather_data = {
            "位置": f"{data['name']}, {data['sys']['country']}",
            "坐标": f"{data['coord']['lat']}, {data['coord']['lon']}",
            "时间": local_time,
            "天气状况": condition_cn,
            "温度": f"{data['main']['temp']}°C",
            "体感温度": f"{data['main']['feels_like']}°C",
            "湿度": f"{data['main']['humidity']}%",
            "风速": f"{data['wind']['speed']} 米/秒",
            "风向": f"{data['wind']['deg']}°",
            "气压": f"{data['main']['pressure']} hPa",
            "云量": f"{data['clouds']['all']}%",
        }
        
        # 处理可选的降雨数据
        if 'rain' in data:
            weather_data['降雨量'] = f"{data['rain'].get('1h', 0)} 毫米"
            
        return weather_data
        
    except requests.RequestException as e:
        return {"错误": f"API请求失败: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"错误": f"数据解析错误: {str(e)}"}
    except Exception as e:
        return {"错误": f"未知错误: {str(e)}"}

# 定义MCP工具
@mcp.tool()
def get_weather(位置: str, api_key: Optional[str] = None, 时区偏移: float = 0) -> Dict[str, Any]:
    """
    获取指定位置的当前天气信息
    
    参数:
        位置: 地理位置名称，如 "北京", "上海"
        api_key: OpenWeatherMap API密钥(可选)
        时区偏移: 时区偏移(小时)，默认为0(UTC)
    
    返回:
        包含天气信息的字典
    """
    return fetch_weather(位置, api_key, 时区偏移)

# 启动服务器
if __name__ == "__main__":
    print("天气 MCP 服务器 正在运行...")
    # 794ed5ee2784d94d6dfaffe0a2c6372a
    if os.environ.get("OPENWEATHER_API_KEY"):
        print("已从环境变量加载API密钥")
    else:
        print("警告: 未设置API密钥环境变量，调用工具时需要提供api_key参数")
    
    mcp.run(transport='stdio')