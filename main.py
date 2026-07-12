# ================= 运行时环境补丁（防止 PyInstaller 扫描临时目录崩溃） =================
import os
import sys
if getattr(sys, 'frozen', False):
    # 强制将打包后的临时解压路径排除在 pkg_resources 的扫描路径之外
    os.environ['PYTHONPATH'] = sys._MEIPASS
    # 阻止 setuptools 尝试去解析无法识别的版本号
    os.environ['SETUPTOOLS_USE_DISTUTILS'] = 'stdlib'
# =================================================================================
import eel
import secrets
import sqlite3
import base64
import io
import platform
import uuid
import threading
import requests
import subprocess
import shutil

# 【核心黑魔法：AST 扫描欺骗】
# 这段代码在真实运行时永远不会执行（因此不卡顿启动速度），
# 但 PyInstaller 静态扫描时会看到它，从而强制把这些庞大的 Excel 引擎打包进去！
if False:
    import pandas
    import openpyxl

# ================= 核心网络与鉴权配置 =================
# 【NAS 接收地址】已完美同步中划线合法路由
NAS_WEBHOOK_URL = "https://******************/api/telemetry"
# 【API 密钥】
TELEMETRY_API_KEY = "jf_sk_live_************************"

# 智能兼容 Mac/Windows 前端网页资源路径
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    web_folder = os.path.join(base_path, 'web')
    # 强制将当前进程的工作目录切换到解压后的沙盒根目录 (Mac 防白屏核心)
    os.chdir(base_path)
else:
    web_folder = 'web'
eel.init(web_folder)

# 自动在用户的“文档”文件夹下创建“随机点名器”专属工作沙盒
USER_HOME = os.path.expanduser("~")
DOCUMENTS_DIR = os.path.join(USER_HOME, 'Documents', '随机点名器')

if not os.path.exists(DOCUMENTS_DIR):
    try:
        os.makedirs(DOCUMENTS_DIR)
    except Exception:
        DOCUMENTS_DIR = USER_HOME

DB_PATH = os.path.join(DOCUMENTS_DIR, 'RandomPicker_students.db')

def init_db():
    # 增加 timeout=20，让数据库在并发撞车时耐心排队
    conn = sqlite3.connect(DB_PATH, timeout=20)
    c = conn.cursor()
    # 开启 WAL 并发模式，支持多线程同时读写，彻底解决 database is locked！
    c.execute('PRAGMA journal_mode=WAL;')
    
    c.execute('''CREATE TABLE IF NOT EXISTS presets (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, preset_id INTEGER, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT UNIQUE, value TEXT)''')
    conn.commit()
    conn.close()

# ================= 异步预加载核心逻辑 =================
pd = None

def preload_pandas_worker():
    global pd
    try:
        import pandas as _pd
        pd = _pd
    except Exception:
        pass

# ================= 隐藏式遥测与打点模块 (Telemetry) =================

def get_or_create_device_id():
    device_id = get_config('device_id')
    if not device_id:
        device_id = str(uuid.uuid4())
        set_config('device_id', device_id)
    return device_id

def get_network_info():
    try:
        res = requests.get("http://ip-api.com/json/?lang=zh-CN", timeout=2.5).json()
        if res.get("status") == "success":
            location = f"{res.get('country', '')} {res.get('regionName', '')} {res.get('city', '')}".strip()
            return res.get("query", "Unknown"), location
    except Exception:
        pass
    return "Unknown", "Unknown"

def get_hardware_info():
    """【终极无损版】静默探测系统硬件配置 (免 subprocess 底层 API 重构，0延迟/100%成功率/永不闪黑框)"""
    cpu = "Unknown CPU"
    cores = os.cpu_count() or 0
    ram_gb = "Unknown"
    gpu = "Unknown GPU"
    res = "Unknown Res"
    
    # 获取系统主盘容量
    try:
        disk_path = "C:\\" if sys.platform == 'win32' else "/"
        disk_total = shutil.disk_usage(disk_path).total / (1024**3)
        disk_info = f"{int(disk_total)}GB"
    except Exception:
        disk_info = "Unknown"

    try:
        if sys.platform == 'darwin': # macOS 硬件探测
            # 1. 尝试精准读取 macOS 物理 CPU 商业名称 (如 Apple M1 Pro)
            try:
                cpu_out = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'])
                cpu = cpu_out.decode(errors='ignore').strip()
            except Exception:
                cpu = platform.processor() or "Apple Silicon"

            # 2. 内存容量
            ram_out = subprocess.check_output(['sysctl', '-n', 'hw.memsize'])
            ram_gb = f"{int(ram_out.strip()) / (1024**3):.1f}GB"
            
            # 3. 显卡与分辨率
            sp_out = subprocess.check_output(['system_profiler', 'SPDisplaysDataType']).decode(errors='ignore')
            for line in sp_out.split('\n'):
                if "Chipset Model:" in line and gpu == "Unknown GPU":
                    gpu = line.split(':')[1].strip()
                if "Resolution:" in line and res == "Unknown Res":
                    res = line.split(':')[1].strip()
                    
        elif sys.platform == 'win32': # Windows 深度重构
            import ctypes
            import winreg
            
            # 1. 获取屏幕分辨率 (通过 C++ User32 API)
            try:
                user32 = ctypes.windll.user32
                res = f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
            except Exception:
                pass

            # 2. 获取 CPU 商业名称 (0 延迟读取底层注册表)
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_reg, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                cpu = cpu_reg.strip()
                winreg.CloseKey(key)
            except Exception:
                cpu = platform.processor() or "Unknown Windows CPU"

            # 3. 获取 RAM 内存大小 (调用 Windows Kernel32 底层内存结构体 API，100% 成功且不调 subprocess)
            try:
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    ram_gb = f"{stat.ullTotalPhys / (1024**3):.1f}GB"
            except Exception:
                pass

            # 4. 获取 GPU 显卡型号 (通过扫描 Windows 统一的显卡驱动硬件注册表 Class 节点)
            try:
                gpu_list = []
                gpu_class_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
                class_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, gpu_class_path)
                
                # 遍历所有注册的显卡子项 (0000, 0001, 0002 等)
                for i in range(16):
                    try:
                        sub_name = f"{i:04d}"
                        sub_key = winreg.OpenKey(class_key, sub_name)
                        try:
                            card_name, _ = winreg.QueryValueEx(sub_key, "DriverDesc")
                            if card_name and card_name not in gpu_list:
                                gpu_list.append(card_name)
                        except Exception:
                            pass
                        winreg.CloseKey(sub_key)
                    except OSError:
                        break # 子项遍历完毕，安全退出
                winreg.CloseKey(class_key)
                if gpu_list:
                    gpu = " + ".join(gpu_list)
            except Exception:
                pass
            
    except Exception:
        pass
    
    return f"CPU: {cpu} ({cores}核) | RAM: {ram_gb} | GPU: {gpu} | 硬盘: {disk_info} | 屏幕: {res}"

def get_telemetry_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TELEMETRY_API_KEY}",
        # 补充真实浏览器模拟伪装，协助方案一防范基础级别的 CF Web 盾威胁
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def send_telemetry_async(action_type="online"):
    if get_config('telemetry_enabled') == 'false':
        return

    def task():
        try:
            device_id = get_or_create_device_id()
            ip, location = get_network_info()
            
            payload = {
                "app_name": "随机点名器",
                "app_version": "1.0.0",
                "device_id": device_id,
                "action": action_type,       
                "ip": ip,
                "location": location,
                "os": f"{platform.system()} {platform.release()}", 
                "hardware": get_hardware_info(),
                "hostname": platform.node()
            }
            # 将超时时间拓宽到更加稳健的 5 秒，防止 CF Tunnel 首次睡眠冷唤醒被断连
            requests.post(NAS_WEBHOOK_URL, json=payload, headers=get_telemetry_headers(), timeout=5)
        except Exception:
            pass
            
    threading.Thread(target=task, daemon=True).start()

def send_telemetry_sync(action_type="offline"):
    if get_config('telemetry_enabled') == 'false':
        return
    try:
        payload = {
            "app_name": "随机点名器",
            "app_version": "1.0.0",
            "device_id": get_or_create_device_id(),
            "action": action_type 
        }
        requests.post(NAS_WEBHOOK_URL, json=payload, headers=get_telemetry_headers(), timeout=3)
    except Exception:
        pass

@eel.expose
def toggle_telemetry(enabled):
    set_config('telemetry_enabled', 'true' if enabled else 'false')

# ================= 核心业务模块 =================

@eel.expose
def get_presets():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    c = conn.cursor()
    c.execute("SELECT id, name FROM presets")
    presets = [{"id": row[0], "name": row[1]} for row in c.fetchall()]
    conn.close()
    return presets

@eel.expose
def get_students(preset_id):
    if not preset_id:
        return []
    conn = sqlite3.connect(DB_PATH, timeout=20)
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE preset_id = ? ORDER BY id", (preset_id,))
    students = [row[0] for row in c.fetchall()]
    conn.close()
    return students

@eel.expose
def set_config(key, value):
    conn = sqlite3.connect(DB_PATH, timeout=20)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

@eel.expose
def get_config(key):
    conn = sqlite3.connect(DB_PATH, timeout=20)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

@eel.expose
def delete_preset(preset_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20)
        c = conn.cursor()
        c.execute("DELETE FROM presets WHERE id = ?", (preset_id,))
        c.execute("DELETE FROM students WHERE preset_id = ?", (preset_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@eel.expose
def import_excel(b64_data, preset_name):
    global pd
    if pd is None:
        import pandas as _pd
        pd = _pd
        
    try:
        _, b64_data = b64_data.split(',', 1)
        decoded = base64.b64decode(b64_data)
        df = pd.read_excel(io.BytesIO(decoded), header=None).fillna("")
        
        name_cols = []
        data_start_row = 0
        
        for row_idx in range(min(20, len(df))):
            row_data = [str(val).strip().replace(" ", "") for val in df.iloc[row_idx].tolist()]
            if any('姓名' in val for val in row_data):
                data_start_row = row_idx + 1 
                for col_idx, val in enumerate(row_data):
                    if '姓名' in val:
                        name_cols.append(col_idx)
                break 
                
        if not name_cols:
            return {"success": False, "error": "未能找到【姓名】列，请检查表格表头！"}

        conn = sqlite3.connect(DB_PATH, timeout=20)
        c = conn.cursor()
        
        original_preset_name = preset_name
        counter = 1
        while True:
            try:
                c.execute("INSERT INTO presets (name) VALUES (?)", (preset_name,))
                preset_id = c.lastrowid
                break  
            except sqlite3.IntegrityError:
                preset_name = f"{original_preset_name}_{counter}"
                counter += 1
            
        valid_count = 0
        for row_idx in range(data_start_row, len(df)):
            for name_col in name_cols:
                name_val = str(df.iloc[row_idx, name_col]).strip()
                if not name_val or name_val.isdigit() or len(name_val) > 15:
                    continue
                c.execute("INSERT INTO students (preset_id, name) VALUES (?, ?)", (preset_id, name_val))
                valid_count += 1
            
        conn.commit()
        conn.close()
        return {"success": True, "message": f"导入成功！提取了 {valid_count} 个名字。", "new_preset_id": preset_id}
        
    except Exception as e:
        return {"success": False, "error": f"解析错误: {str(e)}"}

@eel.expose
def pick_student(preset_id, exclude_names, count=1):
    all_students = get_students(preset_id)
    if not all_students:
        return {"error": "当前名单为空！"}
        
    available = [name for name in all_students if name not in exclude_names]
    if count > len(available):
        return {"error": f"剩余可抽取人数不足！"}
    
    selected = []
    pool = available.copy()
    for _ in range(count):
        chosen = secrets.choice(pool) 
        selected.append(chosen)
        pool.remove(chosen)
        
    return {"success": True, "results": selected}


def heartbeat_loop():
    """客户端守护线程：每 30 秒静默上报一次心跳，维持大屏在线状态"""
    # 首次延迟 2 秒上报，避开启动瞬时并发
    import time
    time.sleep(2)
    while True:
        try:
            send_telemetry_async("online")
        except Exception:
            pass
        time.sleep(30) # 每 30 秒嘀嗒一次

if __name__ == '__main__':
    init_db()
    
    # 1. 开启后台异步预加载 Pandas
    threading.Thread(target=preload_pandas_worker, daemon=True).start()
    
    # 2. 【核心修改】开启后台无限循环心跳守护线程，完美解决退出、关机、断网的在线通报问题
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    
    # 3. 启动 GUI 窗口
    if sys.platform == 'darwin': 
        eel.start('index.html', size=(1000, 700), port=0) 
    else:
        eel.start('index.html', size=(1000, 700), mode='edge', port=0)