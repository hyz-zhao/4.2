#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
城市天气查询小程序
功能：查询城市实时天气、历史记录、快捷复制、API配置管理
作者：AI助手
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
from datetime import datetime


class WeatherData:
    """天气数据实体类"""
    
    def __init__(self, city='', weather='', temperature='', feels_like='', 
                 humidity='', wind='', update_time=''):
        self.city = city
        self.weather = weather
        self.temperature = temperature
        self.feels_like = feels_like
        self.humidity = humidity
        self.wind = wind
        self.update_time = update_time
    
    def to_text(self):
        """格式化天气文本，用于复制和展示"""
        if not self.is_valid():
            return "暂无天气数据"
        
        text = f"""【{self.city}天气】
天气状况：{self.weather}
实时温度：{self.temperature}
体感温度：{self.feels_like}
空气湿度：{self.humidity}
风力风向：{self.wind}
更新时间：{self.update_time}
——来自天气查询小程序"""
        return text
    
    def is_valid(self):
        """校验数据是否完整"""
        return bool(self.city and self.weather)


class WeatherAPI:
    """天气接口请求类"""
    
    def __init__(self, api_key=''):
        self.api_key = api_key
        self.api_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.timeout = 10
    
    def get_weather(self, city_name):
        """请求天气数据"""
        if not self.api_key:
            return None, "请先设置API密钥"
        
        city_code = self._get_city_code(city_name)
        if not city_code:
            return None, f"未找到城市：{city_name}"
        
        try:
            params = {
                'key': self.api_key,
                'city': city_code,
                'extensions': 'base',
                'output': 'json'
            }
            
            response = requests.get(
                self.api_url, 
                params=params, 
                timeout=self.timeout
            )
            
            return self.parse_response(response.json())
            
        except requests.exceptions.Timeout:
            return None, "网络请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return None, "网络连接失败，请检查网络"
        except requests.exceptions.RequestException:
            return None, "网络请求异常，请稍后重试"
        except json.JSONDecodeError:
            return None, "数据解析失败"
        except Exception as e:
            return None, f"未知错误：{str(e)}"
    
    def _get_city_code(self, city_name):
        """获取城市编码（高德地图城市编码表）"""
        city_mapping = {
            '北京': '110000', '北京市': '110000', '京': '110000',
            '天津': '120000', '天津市': '120000', '津': '120000',
            '上海': '310000', '上海市': '310000', '沪': '310000',
            '重庆': '500000', '重庆市': '500000', '渝': '500000',
            '石家庄': '130100', '唐山': '130200', '秦皇岛': '130300',
            '邯郸': '130400', '邢台': '130500', '保定': '130600',
            '张家口': '130700', '承德': '130800', '沧州': '130900',
            '廊坊': '131000', '衡水': '131100',
            '太原': '140100', '大同': '140200', '阳泉': '140300',
            '长治': '140400', '晋城': '140500', '朔州': '140600',
            '晋中': '140700', '运城': '140800', '忻州': '140900',
            '临汾': '141000', '吕梁': '141100',
            '沈阳': '210100', '大连': '210200', '鞍山': '210300',
            '抚顺': '210400', '本溪': '210500', '丹东': '210600',
            '锦州': '210700', '营口': '210800', '阜新': '210900',
            '辽阳': '211000', '盘锦': '211100', '铁岭': '211200',
            '朝阳': '211300', '葫芦岛': '211400',
            '长春': '220100', '吉林': '220200', '四平': '220300',
            '辽源': '220400', '通化': '220500', '白山': '220600',
            '松原': '220700', '白城': '220800',
            '哈尔滨': '230100', '齐齐哈尔': '230200', '鸡西': '230300',
            '鹤岗': '230400', '双鸭山': '230500', '大庆': '230600',
            '伊春': '230700', '佳木斯': '230800', '七台河': '230900',
            '牡丹江': '231000', '黑河': '231100', '绥化': '231200',
            '南京': '320100', '无锡': '320200', '徐州': '320300',
            '常州': '320400', '苏州': '320500', '南通': '320600',
            '连云港': '320700', '淮安': '320800', '盐城': '320900',
            '扬州': '321000', '镇江': '321100', '泰州': '321200',
            '宿迁': '321300',
            '杭州': '330100', '宁波': '330200', '温州': '330300',
            '嘉兴': '330400', '湖州': '330500', '绍兴': '330600',
            '金华': '330700', '衢州': '330800', '舟山': '330900',
            '台州': '331000', '丽水': '331100',
            '合肥': '340100', '芜湖': '340200', '蚌埠': '340300',
            '淮南': '340400', '马鞍山': '340500', '淮北': '340600',
            '铜陵': '340700', '安庆': '340800', '黄山': '341000',
            '滁州': '341100', '阜阳': '341200', '宿州': '341300',
            '六安': '341500', '亳州': '341600', '池州': '341700',
            '宣城': '341800',
            '福州': '350100', '厦门': '350200', '莆田': '350300',
            '三明': '350400', '泉州': '350500', '漳州': '350600',
            '南平': '350700', '龙岩': '350800', '宁德': '350900',
            '南昌': '360100', '景德镇': '360200', '萍乡': '360300',
            '九江': '360400', '新余': '360500', '鹰潭': '360600',
            '赣州': '360700', '吉安': '360800', '宜春': '360900',
            '抚州': '361000', '上饶': '361100',
            '济南': '370100', '青岛': '370200', '淄博': '370300',
            '枣庄': '370400', '东营': '370500', '烟台': '370600',
            '潍坊': '370700', '济宁': '370800', '泰安': '370900',
            '威海': '371000', '日照': '371100', '临沂': '371300',
            '德州': '371400', '聊城': '371500', '滨州': '371600',
            '菏泽': '371700',
            '郑州': '410100', '开封': '410200', '洛阳': '410300',
            '平顶山': '410400', '安阳': '410500', '鹤壁': '410600',
            '新乡': '410700', '焦作': '410800', '濮阳': '410900',
            '许昌': '411000', '漯河': '411100', '三门峡': '411200',
            '南阳': '411300', '商丘': '411400', '信阳': '411500',
            '周口': '411600', '驻马店': '411700',
            '武汉': '420100', '黄石': '420200', '十堰': '420300',
            '宜昌': '420500', '襄阳': '420600', '鄂州': '420700',
            '荆门': '420800', '孝感': '420900', '荆州': '421000',
            '黄冈': '421100', '咸宁': '421200', '随州': '421300',
            '恩施': '422800',
            '长沙': '430100', '株洲': '430200', '湘潭': '430300',
            '衡阳': '430400', '邵阳': '430500', '岳阳': '430600',
            '常德': '430700', '张家界': '430800', '益阳': '430900',
            '郴州': '431000', '永州': '431100', '怀化': '431200',
            '娄底': '431300', '湘西': '433100',
            '广州': '440100', '韶关': '440200', '深圳': '440300',
            '珠海': '440400', '汕头': '440500', '佛山': '440600',
            '江门': '440700', '湛江': '440800', '茂名': '440900',
            '肇庆': '441200', '惠州': '441300', '梅州': '441400',
            '汕尾': '441500', '河源': '441600', '阳江': '441700',
            '清远': '441800', '东莞': '441900', '中山': '442000',
            '潮州': '445100', '揭阳': '445200', '云浮': '445300',
            '南宁': '450100', '柳州': '450200', '桂林': '450300',
            '梧州': '450400', '北海': '450500', '防城港': '450600',
            '钦州': '450700', '贵港': '450800', '玉林': '450900',
            '百色': '451000', '贺州': '451100', '河池': '451200',
            '来宾': '451300', '崇左': '451400',
            '海口': '460100', '三亚': '460200', '三沙': '460300',
            '成都': '510100', '自贡': '510300', '攀枝花': '510400',
            '泸州': '510500', '德阳': '510600', '绵阳': '510700',
            '广元': '510800', '遂宁': '510900', '内江': '511000',
            '乐山': '511100', '南充': '511300', '眉山': '511400',
            '宜宾': '511500', '广安': '511600', '达州': '511700',
            '雅安': '511800', '巴中': '511900', '资阳': '512000',
            '贵阳': '520100', '六盘水': '520200', '遵义': '520300',
            '安顺': '520400', '毕节': '520500', '铜仁': '520600',
            '昆明': '530100', '曲靖': '530300', '玉溪': '530400',
            '保山': '530500', '昭通': '530600', '丽江': '530700',
            '普洱': '530800', '临沧': '530900',
            '拉萨': '540100', '日喀则': '540200', '昌都': '540300',
            '林芝': '540400', '山南': '540500', '那曲': '540600',
            '西安': '610100', '铜川': '610200', '宝鸡': '610300',
            '咸阳': '610400', '渭南': '610500', '延安': '610600',
            '汉中': '610700', '榆林': '610800', '安康': '610900',
            '商洛': '611000',
            '兰州': '620100', '嘉峪关': '620200', '金昌': '620300',
            '白银': '620400', '天水': '620500', '武威': '620600',
            '张掖': '620700', '平凉': '620800', '酒泉': '620900',
            '庆阳': '621000', '定西': '621100', '陇南': '621200',
            '西宁': '630100', '海东': '630200',
            '银川': '640100', '石嘴山': '640200', '吴忠': '640300',
            '固原': '640400', '中卫': '640500',
            '乌鲁木齐': '650100', '克拉玛依': '650200',
            '吐鲁番': '650400', '哈密': '650500',
            '香港': '810000', '澳门': '820000', '台北': '710100',
            '高雄': '710200', '台中': '710300',
        }
        
        city_name = city_name.strip()
        if city_name in city_mapping:
            return city_mapping[city_name]
        
        for name, code in city_mapping.items():
            if city_name in name or name in city_name:
                return code
        
        return city_name
    
    def parse_response(self, resp):
        """解析API返回数据"""
        if resp.get('status') != '1':
            error_info = resp.get('info', '未知错误')
            if error_info == 'INVALID_USER_KEY':
                return None, "API密钥无效，请检查密钥是否正确"
            elif error_info == 'DAILY_QUERY_OVER_LIMIT':
                return None, "API调用次数超限，请明天再试"
            else:
                return None, f"查询失败：{error_info}"
        
        lives = resp.get('lives', [])
        if not lives:
            return None, "未获取到天气数据"
        
        data = lives[0]
        
        weather_data = WeatherData(
            city=data.get('city', ''),
            weather=data.get('weather', ''),
            temperature=f"{data.get('temperature', '')}℃",
            feels_like=f"{data.get('temperature', '')}℃",
            humidity=f"{data.get('humidity', '')}%",
            wind=f"{data.get('winddirection', '')} {data.get('windpower', '')}级",
            update_time=data.get('reporttime', '')
        )
        
        return weather_data, None
    
    def check_key(self):
        """校验密钥有效性"""
        if not self.api_key:
            return False, "API密钥为空"
        
        try:
            params = {
                'key': self.api_key,
                'city': '110000',
                'extensions': 'base',
                'output': 'json'
            }
            
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.timeout
            )
            
            resp = response.json()
            
            if resp.get('status') == '1':
                return True, "API密钥有效"
            else:
                error_info = resp.get('info', '未知错误')
                return False, f"API密钥无效：{error_info}"
                
        except Exception as e:
            return False, f"验证失败：{str(e)}"


class WeatherStore:
    """本地数据存储类"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser('~'), '.weather_app')
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.history_path = os.path.join(self.config_dir, 'history.json')
        self.max_history = 10
        
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def load_config(self):
        """加载API密钥"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('api_key', '')
        except Exception:
            pass
        return ''
    
    def save_config(self, api_key):
        """保存API密钥"""
        try:
            config = {'api_key': api_key}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def load_history(self):
        """加载查询历史"""
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    
    def save_history(self, city):
        """保存查询历史"""
        try:
            history = self.load_history()
            
            if city in history:
                history.remove(city)
            
            history.insert(0, city)
            
            if len(history) > self.max_history:
                history = history[:self.max_history]
            
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def clear_history(self):
        """清空历史"""
        try:
            if os.path.exists(self.history_path):
                os.remove(self.history_path)
            return True
        except Exception:
            return False


class UIManager:
    """GUI界面管理类"""
    
    def __init__(self, root, store, api):
        self.root = root
        self.store = store
        self.api = api
        self.current_weather = None
        
        self._setup_window()
        self._create_widgets()
        self._load_initial_data()
    
    def _setup_window(self):
        """设置窗口属性"""
        self.root.title("城市天气查询")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.root.configure(bg='#f0f0f0')
        
        self._center_window()
    
    def _center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = 500
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """创建界面组件"""
        self._create_search_bar()
        self._create_history_bar()
        self._create_weather_panel()
        self._create_toolbar()
    
    def _create_search_bar(self):
        """创建搜索栏"""
        search_frame = tk.Frame(self.root, bg='#4a90d9', pady=15)
        search_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            search_frame,
            text="🌤️ 城市天气查询",
            font=('微软雅黑', 16, 'bold'),
            bg='#4a90d9',
            fg='white'
        )
        title_label.pack(pady=(0, 10))
        
        input_frame = tk.Frame(search_frame, bg='#4a90d9')
        input_frame.pack()
        
        self.city_entry = tk.Entry(
            input_frame,
            font=('微软雅黑', 12),
            width=20,
            relief=tk.FLAT
        )
        self.city_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        self.city_entry.bind('<Return>', lambda e: self._on_search())
        
        self.search_btn = tk.Button(
            input_frame,
            text="查询",
            font=('微软雅黑', 11),
            bg='#2ecc71',
            fg='white',
            width=8,
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_search
        )
        self.search_btn.pack(side=tk.LEFT, ipady=3)
        
        self.search_btn.bind('<Enter>', lambda e: self.search_btn.configure(bg='#27ae60'))
        self.search_btn.bind('<Leave>', lambda e: self.search_btn.configure(bg='#2ecc71'))
    
    def _create_history_bar(self):
        """创建历史记录栏"""
        history_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        history_frame.pack(fill=tk.X, padx=10)
        
        history_label = tk.Label(
            history_frame,
            text="📍 历史记录：",
            font=('微软雅黑', 10),
            bg='#f0f0f0',
            fg='#666666'
        )
        history_label.pack(anchor=tk.W)
        
        self.history_container = tk.Frame(history_frame, bg='#f0f0f0')
        self.history_container.pack(fill=tk.X, pady=5)
    
    def _create_weather_panel(self):
        """创建天气展示面板"""
        self.weather_frame = tk.Frame(self.root, bg='white', pady=20)
        self.weather_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.weather_canvas = tk.Canvas(
            self.weather_frame,
            bg='white',
            highlightthickness=0
        )
        self.weather_canvas.pack(fill=tk.BOTH, expand=True)
        
        self._show_welcome()
    
    def _create_toolbar(self):
        """创建底部工具栏"""
        toolbar = tk.Frame(self.root, bg='#e0e0e0', pady=10)
        toolbar.pack(fill=tk.X)
        
        btn_frame = tk.Frame(toolbar, bg='#e0e0e0')
        btn_frame.pack()
        
        self.copy_btn = tk.Button(
            btn_frame,
            text="📋 复制天气",
            font=('微软雅黑', 10),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.copy_weather
        )
        self.copy_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        
        self.clear_btn = tk.Button(
            btn_frame,
            text="🗑️ 清空历史",
            font=('微软雅黑', 10),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._clear_history
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
        
        self.settings_btn = tk.Button(
            btn_frame,
            text="⚙️ 设置",
            font=('微软雅黑', 10),
            bg='#9b59b6',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.open_settings
        )
        self.settings_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)
    
    def _load_initial_data(self):
        """加载初始数据"""
        api_key = self.store.load_config()
        self.api.api_key = api_key
        
        self.refresh_history()
    
    def _show_welcome(self):
        """显示欢迎信息"""
        self.weather_canvas.delete('all')
        
        canvas_width = self.weather_frame.winfo_width() or 460
        canvas_height = self.weather_frame.winfo_height() or 350
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2 - 50,
            text="🌤️",
            font=('Segoe UI Emoji', 48),
            fill='#4a90d9'
        )
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2 + 20,
            text="欢迎使用城市天气查询",
            font=('微软雅黑', 14),
            fill='#333333'
        )
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2 + 50,
            text="请输入城市名称查询天气",
            font=('微软雅黑', 10),
            fill='#999999'
        )
    
    def _on_search(self):
        """查询按钮点击事件"""
        city = self.city_entry.get().strip()
        
        if not city:
            messagebox.showwarning("提示", "请输入城市名称")
            return
        
        self.search_btn.configure(text="查询中...", state=tk.DISABLED)
        self.root.update()
        
        weather_data, error = self.api.get_weather(city)
        
        self.search_btn.configure(text="查询", state=tk.NORMAL)
        
        if error:
            self.show_error(error)
        else:
            self.show_weather(weather_data)
            self.store.save_history(city)
            self.refresh_history()
    
    def show_weather(self, data):
        """展示天气数据"""
        self.current_weather = data
        self.weather_canvas.delete('all')
        
        canvas_width = self.weather_frame.winfo_width() or 460
        canvas_height = self.weather_frame.winfo_height() or 350
        
        weather_icons = {
            '晴': '☀️', '多云': '⛅', '阴': '☁️', '雨': '🌧️',
            '小雨': '🌧️', '中雨': '🌧️', '大雨': '🌧️', '暴雨': '⛈️',
            '雪': '🌨️', '小雪': '🌨️', '中雪': '🌨️', '大雪': '🌨️',
            '雾': '🌫️', '霾': '🌫️', '沙尘': '🌪️'
        }
        
        weather_text = data.weather
        icon = '🌤️'
        for key, value in weather_icons.items():
            if key in weather_text:
                icon = value
                break
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            40,
            text=f"{icon} {data.city}",
            font=('微软雅黑', 18, 'bold'),
            fill='#333333'
        )
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            100,
            text=data.temperature,
            font=('微软雅黑', 36, 'bold'),
            fill='#e74c3c'
        )
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            145,
            text=data.weather,
            font=('微软雅黑', 14),
            fill='#666666'
        )
        
        info_y = 190
        info_items = [
            f"🌡️ 体感温度：{data.feels_like}",
            f"💧 空气湿度：{data.humidity}",
            f"🌬️ 风力风向：{data.wind}",
            f"🕐 更新时间：{data.update_time}"
        ]
        
        for item in info_items:
            self.weather_canvas.create_text(
                canvas_width // 2,
                info_y,
                text=item,
                font=('微软雅黑', 11),
                fill='#555555'
            )
            info_y += 35
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            canvas_height - 20,
            text="数据来源：高德地图天气API",
            font=('微软雅黑', 9),
            fill='#aaaaaa'
        )
    
    def show_error(self, msg):
        """显示错误提示"""
        self.current_weather = None
        self.weather_canvas.delete('all')
        
        canvas_width = self.weather_frame.winfo_width() or 460
        canvas_height = self.weather_frame.winfo_height() or 350
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2 - 30,
            text="❌",
            font=('Segoe UI Emoji', 36),
            fill='#e74c3c'
        )
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2 + 20,
            text=msg,
            font=('微软雅黑', 12),
            fill='#e74c3c'
        )
        
        self.weather_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2 + 50,
            text="请检查输入或网络连接",
            font=('微软雅黑', 10),
            fill='#999999'
        )
    
    def refresh_history(self):
        """刷新历史按钮"""
        for widget in self.history_container.winfo_children():
            widget.destroy()
        
        history = self.store.load_history()
        
        if not history:
            no_history = tk.Label(
                self.history_container,
                text="暂无历史记录",
                font=('微软雅黑', 9),
                bg='#f0f0f0',
                fg='#999999'
            )
            no_history.pack(side=tk.LEFT)
            return
        
        for city in history[:10]:
            btn = tk.Button(
                self.history_container,
                text=city,
                font=('微软雅黑', 9),
                bg='#ecf0f1',
                fg='#333333',
                relief=tk.FLAT,
                cursor='hand2',
                command=lambda c=city: self._quick_search(c)
            )
            btn.pack(side=tk.LEFT, padx=3, pady=2)
            
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg='#d5dbdb'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg='#ecf0f1'))
    
    def _quick_search(self, city):
        """快捷查询"""
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self._on_search()
    
    def copy_weather(self):
        """复制天气文本"""
        if not self.current_weather:
            messagebox.showinfo("提示", "暂无天气数据可复制")
            return
        
        text = self.current_weather.to_text()
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("成功", "天气信息已复制到剪贴板")
        except Exception:
            try:
                import pyperclip
                pyperclip.copy(text)
                messagebox.showinfo("成功", "天气信息已复制到剪贴板")
            except Exception:
                messagebox.showerror("错误", "复制失败，请手动复制")
    
    def _clear_history(self):
        """清空历史"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.store.clear_history()
            self.refresh_history()
            messagebox.showinfo("成功", "历史记录已清空")
    
    def open_settings(self):
        """打开设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x250")
        settings_window.resizable(False, False)
        settings_window.configure(bg='#f5f5f5')
        
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 100
        settings_window.geometry(f'+{x}+{y}')
        
        title = tk.Label(
            settings_window,
            text="⚙️ API密钥设置",
            font=('微软雅黑', 14, 'bold'),
            bg='#f5f5f5',
            fg='#333333'
        )
        title.pack(pady=20)
        
        input_frame = tk.Frame(settings_window, bg='#f5f5f5')
        input_frame.pack(pady=10)
        
        tk.Label(
            input_frame,
            text="高德地图API密钥：",
            font=('微软雅黑', 10),
            bg='#f5f5f5'
        ).pack(anchor=tk.W)
        
        api_entry = tk.Entry(
            input_frame,
            font=('微软雅黑', 10),
            width=40,
            show='*'
        )
        api_entry.pack(pady=5, ipady=3)
        
        current_key = self.store.load_config()
        if current_key:
            api_entry.insert(0, current_key)
        
        show_var = tk.BooleanVar(value=False)
        
        def toggle_show():
            if show_var.get():
                api_entry.configure(show='')
            else:
                api_entry.configure(show='*')
        
        show_check = tk.Checkbutton(
            input_frame,
            text="显示密钥",
            variable=show_var,
            command=toggle_show,
            bg='#f5f5f5',
            font=('微软雅黑', 9)
        )
        show_check.pack(anchor=tk.W)
        
        btn_frame = tk.Frame(settings_window, bg='#f5f5f5')
        btn_frame.pack(pady=20)
        
        def save_key():
            key = api_entry.get().strip()
            if not key:
                messagebox.showwarning("提示", "请输入API密钥")
                return
            
            self.api.api_key = key
            valid, msg = self.api.check_key()
            
            if valid:
                self.store.save_config(key)
                messagebox.showinfo("成功", "API密钥保存成功")
                settings_window.destroy()
            else:
                messagebox.showerror("错误", msg)
        
        def get_key():
            import webbrowser
            webbrowser.open("https://console.amap.com/dev/key/app")
        
        save_btn = tk.Button(
            btn_frame,
            text="保存",
            font=('微软雅黑', 10),
            bg='#2ecc71',
            fg='white',
            width=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=save_key
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        get_btn = tk.Button(
            btn_frame,
            text="获取密钥",
            font=('微软雅黑', 10),
            bg='#3498db',
            fg='white',
            width=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=get_key
        )
        get_btn.pack(side=tk.LEFT, padx=10)
        
        tip = tk.Label(
            settings_window,
            text="提示：点击「获取密钥」前往高德地图开放平台申请免费密钥",
            font=('微软雅黑', 9),
            bg='#f5f5f5',
            fg='#999999'
        )
        tip.pack(pady=10)


def main():
    """主函数"""
    root = tk.Tk()
    
    store = WeatherStore()
    api = WeatherAPI()
    
    app = UIManager(root, store, api)
    
    root.mainloop()


if __name__ == '__main__':
    main()
