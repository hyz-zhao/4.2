#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
城市天气查询小程序
纯 Python + Tkinter 原生 GUI
支持高德地图天气 API
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


# ==================== 配置常量 ====================
APP_NAME = "城市天气查询"
APP_VERSION = "1.0.0"
DEFAULT_TIMEOUT = 10  # 请求超时时间（秒）
MAX_HISTORY = 10  # 最大历史记录数


# ==================== WeatherData 类 ====================
class WeatherData:
    """
    天气数据实体类
    存储和格式化天气信息
    """

    def __init__(self):
        self.city: str = ""  # 城市名
        self.weather: str = ""  # 天气状况
        self.temperature: str = ""  # 实时温度
        self.feels_like: str = ""  # 体感温度
        self.humidity: str = ""  # 湿度
        self.wind: str = ""  # 风力风向
        self.update_time: str = ""  # 更新时间

    def to_text(self) -> str:
        """
        格式化天气文本，用于复制和展示
        """
        return (
            f"【{self.city}天气】\n"
            f"天气状况：{self.weather}\n"
            f"实时温度：{self.temperature}\n"
            f"体感温度：{self.feels_like}\n"
            f"相对湿度：{self.humidity}\n"
            f"风力风向：{self.wind}\n"
            f"更新时间：{self.update_time}"
        )

    def is_valid(self) -> bool:
        """
        校验数据是否完整有效
        """
        return all([
            self.city,
            self.weather,
            self.temperature,
            self.update_time
        ])


# ==================== WeatherAPI 类 ====================
class WeatherAPI:
    """
    天气接口请求类
    负责与高德地图天气 API 通信
    """

    def __init__(self, api_key: str = ""):
        self.api_key: str = api_key
        self.api_url: str = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.timeout: int = DEFAULT_TIMEOUT

    def check_key(self) -> bool:
        """
        校验 API 密钥是否已配置
        """
        return bool(self.api_key and self.api_key.strip())

    def get_weather(self, city_name: str) -> WeatherData:
        """
        发送网络请求获取天气数据
        """
        if not self.check_key():
            raise ValueError("请先配置高德地图 API 密钥")

        # 构建请求参数
        params = {
            "key": self.api_key,
            "city": city_name,
            "extensions": "base",  # 获取实时天气
            "output": "JSON"
        }

        try:
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return self.parse_response(response.json(), city_name)

        except requests.exceptions.Timeout:
            raise ConnectionError("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("网络连接失败，请检查网络设置")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"网络请求错误: {str(e)}")

    def parse_response(self, resp: Dict[str, Any], city_name: str) -> WeatherData:
        """
        解析 API 返回数据
        """
        # 检查 API 返回状态
        if resp.get("status") != "1":
            info = resp.get("info", "未知错误")
            if info == "INVALID_KEY":
                raise ValueError("API 密钥无效，请检查密钥配置")
            elif info == "USERKEY_PLAT_NOMATCH":
                raise ValueError("API 密钥与平台不匹配")
            else:
                raise ValueError(f"API 错误: {info}")

        lives = resp.get("lives", [])
        if not lives:
            raise ValueError(f"未找到城市 '{city_name}' 的天气信息，请检查城市名称")

        data = lives[0]
        weather = WeatherData()
        weather.city = data.get("city", city_name)
        weather.weather = data.get("weather", "未知")
        weather.temperature = f"{data.get('temperature', '--')}°C"
        # 高德 API 基础版不返回体感温度，用温度代替
        weather.feels_like = f"{data.get('temperature', '--')}°C"
        weather.humidity = f"{data.get('humidity', '--')}%"
        weather.wind = f"{data.get('winddirection', '--')}风 {data.get('windpower', '--')}级"
        weather.update_time = data.get("reporttime", datetime.now().strftime("%Y-%m-%d %H:%M"))

        return weather


# ==================== WeatherStore 类 ====================
class WeatherStore:
    """
    本地数据存储类
    管理配置文件和历史记录
    """

    def __init__(self):
        # 获取应用数据目录
        self.config_dir = os.path.join(os.path.expanduser("~"), ".weather_app")
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.history_path = os.path.join(self.config_dir, "history.json")
        self.max_history: int = MAX_HISTORY

        # 确保配置目录存在
        self._ensure_dir()

    def _ensure_dir(self):
        """
        确保配置目录存在
        """
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def load_config(self) -> Dict[str, str]:
        """
        加载 API 密钥等配置
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def save_config(self, key: str) -> bool:
        """
        保存 API 密钥
        """
        try:
            config = self.load_config()
            config["api_key"] = key
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存配置失败: {e}")
            return False

    def load_history(self) -> List[str]:
        """
        加载查询历史记录
        """
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        return history[:self.max_history]
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def save_history(self, city: str) -> bool:
        """
        保存查询历史，去重并限制数量
        """
        try:
            history = self.load_history()
            # 如果已存在，先移除
            if city in history:
                history.remove(city)
            # 添加到开头
            history.insert(0, city)
            # 限制数量
            history = history[:self.max_history]

            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存历史记录失败: {e}")
            return False

    def clear_history(self) -> bool:
        """
        清空历史记录
        """
        try:
            if os.path.exists(self.history_path):
                os.remove(self.history_path)
            return True
        except IOError as e:
            print(f"清空历史记录失败: {e}")
            return False


# ==================== UIManager 类 ====================
class UIManager:
    """
    GUI 界面管理类
    负责所有界面组件和交互逻辑
    """

    def __init__(self, root: tk.Tk, api: WeatherAPI, store: WeatherStore):
        self.root = root
        self.api = api
        self.store = store
        self.current_weather: Optional[WeatherData] = None

        # 设置窗口属性
        self.root.title(APP_NAME)
        self.root.geometry("500x600")
        self.root.minsize(400, 500)
        self.root.configure(bg="#f0f0f0")

        # 初始化界面
        self._create_styles()
        self._create_widgets()
        self._load_initial_data()

    def _create_styles(self):
        """
        创建自定义样式
        """
        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 18, "bold"), foreground="#2c3e50")
        style.configure("City.TLabel", font=("微软雅黑", 24, "bold"), foreground="#2980b9")
        style.configure("Temp.TLabel", font=("微软雅黑", 36, "bold"), foreground="#e74c3c")
        style.configure("Info.TLabel", font=("微软雅黑", 12), foreground="#34495e")
        style.configure("Query.TButton", font=("微软雅黑", 11, "bold"))
        style.configure("Action.TButton", font=("微软雅黑", 10))

    def _create_widgets(self):
        """
        创建所有界面组件
        """
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ========== 标题 ==========
        title_label = ttk.Label(main_frame, text="🌤 城市天气查询", style="Title.TLabel")
        title_label.pack(pady=(0, 15))

        # ========== 搜索栏 ==========
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        self.city_entry = ttk.Entry(search_frame, font=("微软雅黑", 12), width=25)
        self.city_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        self.city_entry.bind("<Return>", lambda e: self._on_query())

        query_btn = ttk.Button(
            search_frame,
            text="查询",
            command=self._on_query,
            style="Query.TButton"
        )
        query_btn.pack(side=tk.LEFT, ipadx=15, ipady=3)

        # ========== 历史记录栏 ==========
        history_frame = ttk.LabelFrame(main_frame, text="历史记录", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 15))

        self.history_container = ttk.Frame(history_frame)
        self.history_container.pack(fill=tk.X)

        # ========== 天气展示面板 ==========
        self.weather_frame = ttk.LabelFrame(main_frame, text="天气信息", padding="20")
        self.weather_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 城市名
        self.city_label = ttk.Label(self.weather_frame, text="请输入城市名称", style="City.TLabel")
        self.city_label.pack(pady=(10, 5))

        # 天气图标（用emoji代替）
        self.weather_icon = ttk.Label(self.weather_frame, text="☀️", font=("微软雅黑", 48))
        self.weather_icon.pack(pady=5)

        # 温度
        self.temp_label = ttk.Label(self.weather_frame, text="--°C", style="Temp.TLabel")
        self.temp_label.pack(pady=5)

        # 天气状况
        self.weather_label = ttk.Label(self.weather_frame, text="等待查询...", style="Info.TLabel")
        self.weather_label.pack(pady=5)

        # 详细信息
        info_frame = ttk.Frame(self.weather_frame)
        info_frame.pack(pady=15)

        self.feels_like_label = ttk.Label(info_frame, text="体感: --", style="Info.TLabel")
        self.feels_like_label.pack(side=tk.LEFT, padx=10)

        self.humidity_label = ttk.Label(info_frame, text="湿度: --", style="Info.TLabel")
        self.humidity_label.pack(side=tk.LEFT, padx=10)

        self.wind_label = ttk.Label(info_frame, text="风向: --", style="Info.TLabel")
        self.wind_label.pack(side=tk.LEFT, padx=10)

        # 更新时间
        self.update_label = ttk.Label(self.weather_frame, text="", font=("微软雅黑", 10), foreground="#7f8c8d")
        self.update_label.pack(pady=(10, 0))

        # ========== 工具栏 ==========
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X)

        copy_btn = ttk.Button(
            toolbar_frame,
            text="📋 复制天气",
            command=self.copy_weather,
            style="Action.TButton"
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(
            toolbar_frame,
            text="🗑 清空历史",
            command=self._on_clear_history,
            style="Action.TButton"
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        settings_btn = ttk.Button(
            toolbar_frame,
            text="⚙️ API设置",
            command=self.open_settings,
            style="Action.TButton"
        )
        settings_btn.pack(side=tk.RIGHT)

    def _load_initial_data(self):
        """
        加载初始数据（配置和历史）
        """
        # 加载 API 密钥
        config = self.store.load_config()
        api_key = config.get("api_key", "")
        if api_key:
            self.api.api_key = api_key
        else:
            # 首次运行提示设置 API 密钥
            self.root.after(500, self._show_first_run_tip)

        # 加载历史记录
        self.refresh_history()

    def _show_first_run_tip(self):
        """
        首次运行提示
        """
        messagebox.showinfo(
            "欢迎使用",
            "欢迎使用城市天气查询！\n\n"
            "首次使用需要配置高德地图 API 密钥。\n"
            "请点击右下角的【API设置】按钮进行配置。\n\n"
            "获取密钥方法请参考使用教程。"
        )

    def _on_query(self):
        """
        查询按钮点击事件
        """
        city = self.city_entry.get().strip()
        if not city:
            self.show_error("请输入城市名称")
            return

        # 检查 API 密钥
        if not self.api.check_key():
            self.show_error("请先配置 API 密钥")
            self.open_settings()
            return

        # 显示加载状态
        self._set_loading_state(True)

        # 在后台线程执行查询，避免阻塞界面
        self.root.after(100, lambda: self._do_query(city))

    def _do_query(self, city: str):
        """
        执行天气查询
        """
        try:
            weather = self.api.get_weather(city)
            self.current_weather = weather
            self.show_weather(weather)
            self.store.save_history(weather.city)
            self.refresh_history()
        except (ValueError, ConnectionError) as e:
            self.show_error(str(e))
        finally:
            self._set_loading_state(False)

    def _set_loading_state(self, loading: bool):
        """
        设置加载状态
        """
        if loading:
            self.city_label.config(text="正在查询...")
            self.weather_icon.config(text="⏳")
            self.temp_label.config(text="请稍候")
            self.weather_label.config(text="")
        # 按钮状态由用户操作控制，这里简化处理

    def _get_weather_emoji(self, weather: str) -> str:
        """
        根据天气状况返回对应的 emoji
        """
        weather_map = {
            "晴": "☀️",
            "多云": "⛅",
            "阴": "☁️",
            "小雨": "🌦️",
            "中雨": "🌧️",
            "大雨": "🌧️",
            "暴雨": "⛈️",
            "雷阵雨": "⛈️",
            "雪": "🌨️",
            "小雪": "🌨️",
            "中雪": "🌨️",
            "大雪": "❄️",
            "雾": "🌫️",
            "霾": "😷",
            "沙尘": "🌪️",
            "风": "💨",
        }
        for key, emoji in weather_map.items():
            if key in weather:
                return emoji
        return "🌡️"

    def show_weather(self, data: WeatherData):
        """
        渲染天气数据到界面
        """
        if not data.is_valid():
            self.show_error("天气数据不完整")
            return

        self.city_label.config(text=data.city)
        self.weather_icon.config(text=self._get_weather_emoji(data.weather))
        self.temp_label.config(text=data.temperature)
        self.weather_label.config(text=data.weather)
        self.feels_like_label.config(text=f"体感: {data.feels_like}")
        self.humidity_label.config(text=f"湿度: {data.humidity}")
        self.wind_label.config(text=f"风向: {data.wind}")
        self.update_label.config(text=f"更新时间: {data.update_time}")

    def show_error(self, msg: str):
        """
        显示错误提示
        """
        messagebox.showerror("提示", msg)

    def refresh_history(self):
        """
        刷新历史记录按钮
        """
        # 清空现有按钮
        for widget in self.history_container.winfo_children():
            widget.destroy()

        history = self.store.load_history()
        if not history:
            empty_label = ttk.Label(self.history_container, text="暂无历史记录", foreground="#95a5a6")
            empty_label.pack()
            return

        for city in history:
            btn = tk.Button(
                self.history_container,
                text=city,
                font=("微软雅黑", 10),
                bg="#ecf0f1",
                fg="#2c3e50",
                activebackground="#3498db",
                activeforeground="white",
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda c=city: self._on_history_click(c)
            )
            btn.pack(side=tk.LEFT, padx=3, pady=2, ipadx=8, ipady=2)

    def _on_history_click(self, city: str):
        """
        历史记录按钮点击事件
        """
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self._on_query()

    def _on_clear_history(self):
        """
        清空历史记录按钮点击事件
        """
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            if self.store.clear_history():
                self.refresh_history()
                messagebox.showinfo("成功", "历史记录已清空")
            else:
                self.show_error("清空历史记录失败")

    def copy_weather(self):
        """
        复制天气文本到剪贴板
        """
        if not self.current_weather or not self.current_weather.is_valid():
            self.show_error("没有可复制的天气信息，请先查询")
            return

        text = self.current_weather.to_text()

        try:
            # 尝试使用 pyperclip
            import pyperclip
            pyperclip.copy(text)
        except ImportError:
            # 备用方案：使用 tkinter 的剪贴板
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

        messagebox.showinfo("成功", "天气信息已复制到剪贴板")

    def open_settings(self):
        """
        打开 API 密钥设置窗口
        """
        settings_window = tk.Toplevel(self.root)
        settings_window.title("API 设置")
        settings_window.geometry("400x250")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # 居中显示
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() - 400) // 2
        y = (settings_window.winfo_screenheight() - 250) // 2
        settings_window.geometry(f"400x250+{x}+{y}")

        frame = ttk.Frame(settings_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # 说明文字
        ttk.Label(
            frame,
            text="高德地图 API 密钥设置",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            frame,
            text="请输入您的高德地图 Web服务 API 密钥：",
            font=("微软雅黑", 10)
        ).pack(anchor=tk.W)

        # 密钥输入框
        key_var = tk.StringVar(value=self.api.api_key)
        entry = ttk.Entry(frame, textvariable=key_var, font=("微软雅黑", 11), width=40)
        entry.pack(fill=tk.X, pady=10, ipady=5)

        # 帮助链接
        help_text = "如何获取密钥？访问 https://lbs.amap.com/ 注册并申请 Web服务 Key"
        help_label = tk.Label(
            frame,
            text=help_text,
            font=("微软雅黑", 9),
            fg="#3498db",
            cursor="hand2",
            wraplength=360
        )
        help_label.pack(pady=(0, 10))

        def open_link(event):
            import webbrowser
            webbrowser.open("https://lbs.amap.com/api/webservice/guide/create-project/get-key")

        help_label.bind("<Button-1>", open_link)

        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        def save():
            key = key_var.get().strip()
            if not key:
                messagebox.showerror("错误", "请输入 API 密钥")
                return
            self.api.api_key = key
            if self.store.save_config(key):
                messagebox.showinfo("成功", "API 密钥已保存")
                settings_window.destroy()
            else:
                messagebox.showerror("错误", "保存失败")

        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(btn_frame, text="取消", command=settings_window.destroy).pack(side=tk.RIGHT)


# ==================== 主程序入口 ====================
def main():
    """
    程序入口函数
    """
    # 创建主窗口
    root = tk.Tk()

    # 设置 DPI 感知（Windows 高分辨率屏幕适配）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    # 创建核心对象
    store = WeatherStore()
    api = WeatherAPI()
    app = UIManager(root, api, store)

    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()
