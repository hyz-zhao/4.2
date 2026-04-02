# -*- coding: utf-8 -*-
"""
城市天气查询小程序
作者：TRAE项目
日期：2026-04-02
功能：查询城市天气、保存历史记录、配置管理等
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime


class WeatherData:
    """天气数据实体类"""
    
    def __init__(self, city="", weather="", temperature="", feels_like="", humidity="", wind="", update_time=""):
        self.city = city
        self.weather = weather
        self.temperature = temperature
        self.feels_like = feels_like
        self.humidity = humidity
        self.wind = wind
        self.update_time = update_time
    
    def to_text(self):
        """格式化天气文本用于复制"""
        text = f"城市：{self.city}\n"
        text += f"天气状况：{self.weather}\n"
        text += f"实时温度：{self.temperature}℃\n"
        text += f"体感温度：{self.feels_like}℃\n"
        text += f"湿度：{self.humidity}%\n"
        text += f"风力风向：{self.wind}\n"
        text += f"更新时间：{self.update_time}"
        return text
    
    def is_valid(self):
        """校验数据是否完整"""
        return all([self.city, self.weather, self.temperature])


class WeatherAPI:
    """天气接口请求类"""
    
    def __init__(self, api_key="", api_url="https://restapi.amap.com/v3/weather/weatherInfo", timeout=10):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
    
    def get_weather(self, city_name):
        """请求天气数据"""
        if not self.check_key():
            raise Exception("API密钥无效，请重新配置")
        
        params = {
            "key": self.api_key,
            "city": city_name,
            "extensions": "base"
        }
        
        try:
            resp = requests.get(self.api_url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return self.parse_response(resp.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败：{str(e)}")
    
    def parse_response(self, resp):
        """解析API返回数据"""
        if resp.get("status") != "1":
            raise Exception(f"API返回错误：{resp.get('info', '未知错误')}")
        
        lives = resp.get("lives", [])
        if not lives:
            raise Exception("未找到该城市的天气数据")
        
        data = lives[0]
        return WeatherData(
            city=data.get("city", ""),
            weather=data.get("weather", ""),
            temperature=data.get("temperature", ""),
            feels_like=data.get("feelsLike", ""),
            humidity=data.get("humidity", ""),
            wind=f"{data.get('windDirection', '')}风 {data.get('windPower', '')}级",
            update_time=data.get("reportTime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    def check_key(self):
        """校验密钥有效性"""
        return bool(self.api_key and len(self.api_key) > 10)


class WeatherStore:
    """本地数据存储类"""
    
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.weather_app")
        self.config_path = os.path.join(config_dir, "config.json")
        self.history_path = os.path.join(config_dir, "history.json")
        self.max_history = 10
        self.config_dir = config_dir
        self._ensure_dir()
    
    def _ensure_dir(self):
        """确保配置目录存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def load_config(self):
        """加载API密钥"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("api_key", "")
            except Exception:
                pass
        return ""
    
    def save_config(self, key):
        """保存API密钥"""
        config = {"api_key": key}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        """加载查询历史"""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def save_history(self, city):
        """保存查询历史"""
        history = self.load_history()
        if city in history:
            history.remove(city)
        history.insert(0, city)
        history = history[:self.max_history]
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def clear_history(self):
        """清空历史"""
        if os.path.exists(self.history_path):
            os.remove(self.history_path)


class UIManager:
    """GUI界面管理类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("城市天气查询")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.store = WeatherStore()
        self.api = WeatherAPI(api_key=self.store.load_config())
        self.current_weather = None
        
        self._setup_ui()
        self.refresh_history()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 搜索栏
        self._create_search_bar(main_frame)
        
        # 2. 历史记录栏
        self._create_history_bar(main_frame)
        
        # 3. 天气展示面板
        self._create_weather_panel(main_frame)
        
        # 4. 工具栏
        self._create_toolbar(main_frame)
    
    def _create_search_bar(self, parent):
        """创建搜索栏"""
        search_frame = ttk.LabelFrame(parent, text="城市查询", padding="10")
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="城市名：").pack(side=tk.LEFT)
        
        self.city_entry = ttk.Entry(search_frame, width=30)
        self.city_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.city_entry.bind("<Return>", lambda e: self.on_search())
        
        self.search_btn = ttk.Button(search_frame, text="查询", command=self.on_search)
        self.search_btn.pack(side=tk.LEFT)
    
    def _create_history_bar(self, parent):
        """创建历史记录栏"""
        history_frame = ttk.LabelFrame(parent, text="历史记录", padding="10")
        history_frame.pack(fill=tk.X, pady=5)
        
        self.history_container = ttk.Frame(history_frame)
        self.history_container.pack(fill=tk.X)
    
    def _create_weather_panel(self, parent):
        """创建天气展示面板"""
        weather_frame = ttk.LabelFrame(parent, text="天气详情", padding="10")
        weather_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.weather_text = tk.Text(weather_frame, height=15, state=tk.DISABLED)
        self.weather_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.weather_text, command=self.weather_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.weather_text.config(yscrollcommand=scrollbar.set)
    
    def _create_toolbar(self, parent):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(parent, padding="5")
        toolbar_frame.pack(fill=tk.X, pady=5)
        
        self.copy_btn = ttk.Button(toolbar_frame, text="复制天气", command=self.copy_weather)
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_history_btn = ttk.Button(toolbar_frame, text="清空历史", command=self.clear_history)
        self.clear_history_btn.pack(side=tk.LEFT, padx=5)
        
        self.settings_btn = ttk.Button(toolbar_frame, text="设置密钥", command=self.open_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5)
    
    def on_search(self):
        """查询按钮点击事件"""
        city = self.city_entry.get().strip()
        if not city:
            self.show_error("请输入城市名称")
            return
        
        try:
            self.current_weather = self.api.get_weather(city)
            if self.current_weather.is_valid():
                self.show_weather(self.current_weather)
                self.store.save_history(city)
                self.refresh_history()
            else:
                self.show_error("数据不完整，请重试")
        except Exception as e:
            self.show_error(str(e))
    
    def show_weather(self, data):
        """渲染天气数据"""
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete(1.0, tk.END)
        self.weather_text.insert(tk.END, data.to_text())
        self.weather_text.config(state=tk.DISABLED)
    
    def show_error(self, msg):
        """显示错误提示"""
        messagebox.showerror("错误", msg)
    
    def refresh_history(self):
        """刷新历史按钮"""
        for widget in self.history_container.winfo_children():
            widget.destroy()
        
        history = self.store.load_history()
        for city in history:
            btn = ttk.Button(self.history_container, text=city, width=8, 
                            command=lambda c=city: self._search_history_city(c))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
    
    def _search_history_city(self, city):
        """点击历史城市按钮"""
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self.on_search()
    
    def copy_weather(self):
        """复制天气文本"""
        if self.current_weather and self.current_weather.is_valid():
            text = self.current_weather.to_text()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("提示", "天气信息已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "请先查询天气")
    
    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空历史记录吗？"):
            self.store.clear_history()
            self.refresh_history()
    
    def open_settings(self):
        """打开API密钥设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("API密钥设置")
        settings_window.geometry("400x150")
        settings_window.resizable(False, False)
        
        ttk.Label(settings_window, text="高德地图天气API密钥：", font=("Arial", 10)).pack(pady=20)
        
        key_entry = ttk.Entry(settings_window, width=40)
        key_entry.pack(pady=5)
        key_entry.insert(0, self.api.api_key)
        
        def save_key():
            new_key = key_entry.get().strip()
            if new_key:
                self.api.api_key = new_key
                self.store.save_config(new_key)
                messagebox.showinfo("提示", "API密钥已保存")
                settings_window.destroy()
            else:
                messagebox.showwarning("提示", "请输入API密钥")
        
        ttk.Button(settings_window, text="保存", command=save_key).pack(pady=10)


def main():
    """主函数"""
    root = tk.Tk()
    app = UIManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
