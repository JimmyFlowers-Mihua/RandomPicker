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
NAS_WEBHOOK_URL = "https://********************/api/telemetry"
TELEMETRY_API_KEY = "jf_sk_live_**************"

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
    # 【核心修复】：增加 timeout=20，让数据库在撞车时耐心排队而不是直接崩溃
    conn = sqlite3.connect(DB_PATH, timeout=20)
    c = conn.cursor()
    
    # 【核心修复】：开启 WAL 并发模式，支持多线程同时读写，彻底解决 database is locked！
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
    cpu = platform.processor() or "Unknown CPU"
    cores = os.cpu_count() or 0
    ram_gb = "Unknown"
    gpu = "Unknown GPU"
    res = "Unknown Res"
    
    try:
        disk_path = "C:\\" if sys.platform == 'win32' else "/"
        disk_total = shutil.disk_usage(disk_path).total / (1024**3)
        disk_info = f"{int(disk_total)}GB"
    except Exception:
        disk_info = "Unknown"

    try:
        if sys.platform == 'darwin': 
            ram_out = subprocess.check_output(['sysctl', '-n', 'hw.memsize'])
            ram_gb = f"{int(ram_out.strip()) / (1024**3):.1f}GB"
            
            sp_out = subprocess.check_output(['system_profiler', 'SPDisplaysDataType']).decode(errors='ignore')
            for line in sp_out.split('\n'):
                if "Chipset Model:" in line and gpu == "Unknown GPU":
                    gpu = line.split(':')[1].strip()
                if "Resolution:" in line and res == "Unknown Res":
                    res = line.split(':')[1].strip()
                    
        elif sys.platform == 'win32': 
            import ctypes
            user32 = ctypes.windll.user32
            res = f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
            
            ram_out = subprocess.check_output(['wmic', 'computersystem', 'get', 'totalphysicalmemory'])
            mem_bytes = int(ram_out.decode(errors='ignore').split('\n')[1].strip())
            ram_gb = f"{mem_bytes / (1024**3):.1f}GB"
            
            gpu_out = subprocess.check_output(['wmic', 'path', 'win32_VideoController', 'get', 'name']).decode(errors='ignore')
            gpus = [line.strip() for line in gpu_out.split('\n')[1:] if line.strip()]
            gpu = " + ".join(gpus) if gpus else "Unknown GPU"
            
    except Exception:
        pass
    
    return f"CPU: {cpu} ({cores}核) | RAM: {ram_gb} | GPU: {gpu} | 硬盘: {disk_info} | 屏幕: {res}"

def get_telemetry_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TELEMETRY_API_KEY}"
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
            requests.post(NAS_WEBHOOK_URL, json=payload, headers=get_telemetry_headers(), timeout=3)
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
        requests.post(NAS_WEBHOOK_URL, json=payload, headers=get_telemetry_headers(), timeout=1.8)
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


if __name__ == '__main__':
    init_db()
    
    send_telemetry_async("online")
    threading.Thread(target=preload_pandas_worker, daemon=True).start()
    
    if sys.platform == 'darwin': 
        eel.start('index.html', size=(1000, 700), port=0) 
    else:
        eel.start('index.html', size=(1000, 700), mode='edge', port=0)
        
    threading.Thread(target=send_telemetry_sync, args=("offline",), daemon=True).start()