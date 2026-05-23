import time
import ctypes
import threading
import win32api
import win32con
import tkinter as tk
from tkinter import scrolledtext
import queue

# ==========================================
# Windows 底層硬體輸入結構定義 (ctypes)
# ==========================================
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_ushort), ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput), ("ki", KeyBdInput), ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

def send_physical_key(scan_code, is_key_up=False):
    flags = win32con.KEYEVENTF_SCANCODE
    if is_key_up: flags |= win32con.KEYEVENTF_KEYUP
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, scan_code, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def press_and_release(scan_code, duration=0.05):
    send_physical_key(scan_code, is_key_up=False)
    time.sleep(duration)
    send_physical_key(scan_code, is_key_up=True)
    time.sleep(duration)

# ==========================================
# 參數與按鍵設定
# ==========================================
TOGGLE_5_VK = 0x35      # 數字鍵「5」
TOGGLE_6_VK = 0x36      # 數字鍵「6」
TOGGLE_7_VK = 0x37      # 數字鍵「7」
EXIT_VK = 0xC0          # 「~」鍵

W_SCAN = 0x11           # W 鍵
ENTER_SCAN = 0x1C       # Enter 鍵
X_SCAN = 0x2D           # X 鍵

# 運行狀態控制
running_func5 = False           
running_func6 = False           
running_func7 = False           
exit_program = False

# 參數設定 (透過 UI 更新，功能 6 已完全解構)
configs = {
    "f5_dur": 30.0,
    
    "f6_wait_e1": 0.5,    # 步驟 1: 第一個 Enter 後的等待時間
    "f6_w_dur": 40.0,     # 步驟 2: W 鍵按住的時間
    "f6_wait_w": 0.5,     # 步驟 2: W 鍵放開後的等待時間
    "f6_wait_x": 1.0,     # 步驟 3: X 鍵按下後的等待時間
    "f6_cooldown": 10.0,  # 步驟 4: 第二個 Enter 後的冷卻等待時間
    
    "f7_interval": 0.5
}

# 用於將背景 Log 傳遞到 UI 的佇列
log_queue = queue.Queue()

def log_msg(msg):
    """取代原本的 print，將訊息推入佇列供介面讀取"""
    log_queue.put(msg)
    print(msg) 

# ==========================================
# 背景巨集邏輯執行緒
# ==========================================
def macro_loop_func5():
    global running_func5, exit_program
    while not exit_program:
        if running_func5:
            dur = configs["f5_dur"]
            log_msg(f"===> [功能 5] 開始一輪 {dur} 秒的無限流 W 鍵輸入...")
            start_time = time.time()
            send_physical_key(W_SCAN, is_key_up=False)
            
            while time.time() - start_time < dur:
                if not running_func5 or exit_program: break
                send_physical_key(W_SCAN, is_key_up=False)
                time.sleep(0.005) 
            
            send_physical_key(W_SCAN, is_key_up=True)
            if running_func5 and not exit_program:
                log_msg(f"===> [功能 5] {dur} 秒時間到，停頓 0.1 秒...")
                time.sleep(0.1)
        else:
            time.sleep(0.02)

def macro_loop_func6():
    """功能 6：每個動作全獨立，間隔皆可調"""
    global running_func6, exit_program
    while not exit_program:
        if running_func6:
            # 即時抓取 UI 上設定的秒數
            wait_e1 = configs["f6_wait_e1"]
            w_dur = configs["f6_w_dur"]
            wait_w = configs["f6_wait_w"]
            wait_x = configs["f6_wait_x"]
            cooldown = configs["f6_cooldown"]
            
            log_msg("\n===> [功能 6] 啟動新一輪循環...")
            
            # ---------------- 步驟 1：第一個 Enter ----------------
            log_msg("-> 步驟 1: 按下 第一個 Enter")
            press_and_release(ENTER_SCAN)
            if not running_func6 or exit_program: continue
            
            log_msg(f"   [等待 {wait_e1} 秒...]")
            wait_start = time.time()
            while time.time() - wait_start < wait_e1:
                if not running_func6 or exit_program: break
                time.sleep(0.1)
            if not running_func6 or exit_program: continue
            
            # ---------------- 步驟 2：長按 W 鍵 ----------------
            log_msg(f"-> 步驟 2: W 鍵按住 {w_dur} 秒...")
            start_time = time.time()
            send_physical_key(W_SCAN, is_key_up=False)
            while time.time() - start_time < w_dur:
                if not running_func6 or exit_program: break
                send_physical_key(W_SCAN, is_key_up=False) 
                time.sleep(0.005)
            send_physical_key(W_SCAN, is_key_up=True)   
            if not running_func6 or exit_program: continue
            
            log_msg(f"   [等待 {wait_w} 秒...]")
            wait_start = time.time()
            while time.time() - wait_start < wait_w:
                if not running_func6 or exit_program: break
                time.sleep(0.1)
            if not running_func6 or exit_program: continue
            
            # ---------------- 步驟 3：按下 X 鍵 ----------------
            log_msg("-> 步驟 3: 按下 X")
            press_and_release(X_SCAN)
            if not running_func6 or exit_program: continue
            
            log_msg(f"   [等待 {wait_x} 秒...]")
            wait_start = time.time()
            while time.time() - wait_start < wait_x:
                if not running_func6 or exit_program: break
                time.sleep(0.1)
            if not running_func6 or exit_program: continue
            
            # ---------------- 步驟 4：第二個 Enter ----------------
            log_msg("-> 步驟 4: 按下 第二個 Enter")
            press_and_release(ENTER_SCAN)
            
            # ---------------- 步驟 5：結尾冷卻等待 ----------------
            if running_func6 and not exit_program:
                log_msg(f"-> 步驟 5: 進入 {cooldown} 秒冷卻等待期...")
                wait_start = time.time()
                while time.time() - wait_start < cooldown:
                    if not running_func6 or exit_program: break
                    time.sleep(0.1)
        else:
            time.sleep(0.02)

def macro_loop_func7():
    global running_func7, exit_program
    while not exit_program:
        if running_func7:
            interval = configs["f7_interval"]
            log_msg("===> [功能 7] 發送一次 Enter...")
            press_and_release(ENTER_SCAN, duration=0.05)
            
            wait_start = time.time()
            while time.time() - wait_start < interval:
                if not running_func7 or exit_program: break
                time.sleep(0.05)
        else:
            time.sleep(0.02)

def key_listener(app_quit_callback):
    global running_func5, running_func6, running_func7, exit_program
    
    last_5 = False; last_6 = False; last_7 = False
    
    while not exit_program:
        s5 = bool(win32api.GetAsyncKeyState(TOGGLE_5_VK) & 0x8000)
        s6 = bool(win32api.GetAsyncKeyState(TOGGLE_6_VK) & 0x8000)
        s7 = bool(win32api.GetAsyncKeyState(TOGGLE_7_VK) & 0x8000)
        s_exit = bool(win32api.GetAsyncKeyState(EXIT_VK) & 0x8000)
        
        if s5 and not last_5:
            running_func6 = running_func7 = False
            running_func5 = not running_func5
            log_msg(f"\n[狀態變更] 功能 5 已 {'【開啟】' if running_func5 else '【關閉】'}")
            if not running_func5: send_physical_key(W_SCAN, is_key_up=True)
                
        if s6 and not last_6:
            running_func5 = running_func7 = False
            running_func6 = not running_func6
            log_msg(f"\n[狀態變更] 功能 6 已 {'【開啟】' if running_func6 else '【關閉】'}")
            if not running_func6:
                for k in [W_SCAN, ENTER_SCAN, X_SCAN]: send_physical_key(k, is_key_up=True)
                
        if s7 and not last_7:
            running_func5 = running_func6 = False
            running_func7 = not running_func7
            log_msg(f"\n[狀態變更] 功能 7 已 {'【開啟】' if running_func7 else '【關閉】'}")
            if not running_func7: send_physical_key(ENTER_SCAN, is_key_up=True)
            
        if s_exit:
            log_msg("\n[系統通知] 接收到退出指令，安全關閉中...")
            app_quit_callback() 
            break
            
        last_5, last_6, last_7 = s5, s6, s7
        time.sleep(0.01)

def cleanup_and_exit():
    global running_func5, running_func6, running_func7, exit_program
    running_func5 = running_func6 = running_func7 = False
    exit_program = True
    for k in [W_SCAN, ENTER_SCAN, X_SCAN]: 
        send_physical_key(k, is_key_up=True)

# ==========================================
# Tkinter 簡約設計感圖形化介面
# ==========================================
class MacroGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("巨集控制核心")
        self.root.geometry("480x780") # 視窗稍微拉高以容納新參數
        self.root.configure(bg="#22252A")
        
        # 顏色設定
        self.bg_color = "#22252A"
        self.card_color = "#2C313A"
        self.text_color = "#ABB2BF"
        self.accent_color = "#61AFEF"
        
        self.font_title = ("Segoe UI", 16, "bold")
        self.font_normal = ("Segoe UI", 10)
        self.font_code = ("Consolas", 9)
        
        self.build_ui()
        self.init_logs()
        self.update_logs_from_queue()
        
    def build_ui(self):
        # Top Frame (Title & Topmost Checkbox)
        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_lbl = tk.Label(top_frame, text="Macro Control Center", fg=self.accent_color, bg=self.bg_color, font=self.font_title)
        title_lbl.pack(side="left")
        
        self.topmost_var = tk.BooleanVar(value=False)
        topmost_chk = tk.Checkbutton(top_frame, text="置頂視窗", variable=self.topmost_var, command=self.toggle_topmost,
                                     bg=self.bg_color, fg=self.text_color, selectcolor=self.card_color, 
                                     activebackground=self.bg_color, activeforeground=self.text_color, bd=0)
        topmost_chk.pack(side="right")
        
        # Settings Card
        settings_frame = tk.Frame(self.root, bg=self.card_color, bd=0, relief="flat")
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        self.vars = {}
        # 建立參數調整區
        self.add_param_row(settings_frame, "【功能 5】W 鍵長按時間 (秒)", "f5_dur", configs["f5_dur"])
        self.add_separator(settings_frame)
        
        # 功能 6 解構版參數區
        self.add_param_row(settings_frame, "【功能 6】第一 Enter 後等待 (秒)", "f6_wait_e1", configs["f6_wait_e1"])
        self.add_param_row(settings_frame, "【功能 6】W 鍵按住時間 (秒)", "f6_w_dur", configs["f6_w_dur"])
        self.add_param_row(settings_frame, "【功能 6】W 鍵放開後等待 (秒)", "f6_wait_w", configs["f6_wait_w"])
        self.add_param_row(settings_frame, "【功能 6】X 鍵按下後等待 (秒)", "f6_wait_x", configs["f6_wait_x"])
        self.add_param_row(settings_frame, "【功能 6】第二 Enter 後冷卻 (秒)", "f6_cooldown", configs["f6_cooldown"])
        
        self.add_separator(settings_frame)
        self.add_param_row(settings_frame, "【功能 7】Enter 間隔時間 (秒)", "f7_interval", configs["f7_interval"])
        
        # Console Area
        console_frame = tk.Frame(self.root, bg=self.bg_color)
        console_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        console_lbl = tk.Label(console_frame, text="運行日誌 (Terminal)", fg=self.text_color, bg=self.bg_color, font=self.font_normal)
        console_lbl.pack(anchor="w", pady=(0, 5))
        
        self.log_area = scrolledtext.ScrolledText(console_frame, bg="#1E2024", fg="#98C379", font=self.font_code, 
                                                  bd=0, insertbackground="white", state="disabled", wrap="word")
        self.log_area.pack(fill="both", expand=True)

    def add_param_row(self, parent, label_text, config_key, default_val):
        row = tk.Frame(parent, bg=self.card_color)
        row.pack(fill="x", padx=15, pady=6) # 微調間距讓元件不會太擠
        
        lbl = tk.Label(row, text=label_text, bg=self.card_color, fg=self.text_color, font=self.font_normal)
        lbl.pack(side="left")
        
        var = tk.StringVar(value=str(default_val))
        var.trace_add("write", lambda *args, k=config_key, v=var: self.on_param_change(k, v))
        self.vars[config_key] = var
        
        entry = tk.Entry(row, textvariable=var, width=6, bg="#1E2024", fg="white", bd=0, 
                         justify="center", font=self.font_normal)
        entry.pack(side="right", ipady=3)

    def add_separator(self, parent):
        sep = tk.Frame(parent, bg="#3E4451", height=1)
        sep.pack(fill="x", padx=15, pady=2)

    def on_param_change(self, key, string_var):
        """當介面輸入框改變時，即時更新全域 configs"""
        try:
            val = float(string_var.get())
            if val >= 0:
                configs[key] = val
        except ValueError:
            pass

    def toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def update_logs_from_queue(self):
        has_new = False
        self.log_area.config(state="normal")
        while not log_queue.empty():
            msg = log_queue.get()
            self.log_area.insert(tk.END, msg + "\n")
            has_new = True
        
        if has_new:
            self.log_area.see(tk.END)
        self.log_area.config(state="disabled")
        
        self.root.after(50, self.update_logs_from_queue)

    def init_logs(self):
        log_msg("========================================")
        log_msg(" 核心啟動成功！(自訂步調進階版)")
        log_msg(" 按【 5 】切換 功能 5")
        log_msg(" 按【 6 】切換 功能 6 (全獨立步驟版)")
        log_msg(" 按【 7 】切換 功能 7")
        log_msg(" 按【 ~ 】安全關閉程式")
        log_msg(" 提示: UI 的秒數調整會即刻生效於下一回合。")
        log_msg("========================================")

def on_closing():
    cleanup_and_exit()
    root.destroy()

def trigger_close_from_hotkey():
    cleanup_and_exit()
    root.after(500, root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = MacroGUI(root)
    
    threading.Thread(target=macro_loop_func5, daemon=True).start()
    threading.Thread(target=macro_loop_func6, daemon=True).start()
    threading.Thread(target=macro_loop_func7, daemon=True).start()
    threading.Thread(target=key_listener, args=(trigger_close_from_hotkey,), daemon=True).start()
    
    root.mainloop()