import pandas as pd
import json
import os
import sys
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
import webview
import tempfile
import uuid  # <--- YENİ EKLENDİ: Tarayıcı önbelleğini kırmak için!

# --- YARDIMCI FONKSİYONLAR ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_real_path(filename):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), filename)
    return os.path.abspath(filename)

def get_image_data(filename):
    full_path = resource_path(filename)
    if not os.path.exists(full_path):
        full_path = filename 
    if os.path.exists(full_path):
        try:
            with open(full_path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        except:
            pass
    return "https://via.placeholder.com/300x200?text=Gorsel+Yok"

# --- HTML VE PYTHON KÖPRÜSÜ (API) ---
class Api:
    def save_ui_settings(self, settings_json):
        try:
            with open(get_real_path("ui_ayarlar.json"), "w", encoding="utf-8") as f:
                f.write(settings_json)
            return "OK"
        except Exception as e:
            return str(e)

    def load_ui_settings(self):
        path = get_real_path("ui_ayarlar.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return "{}"
        return "{}"

# --- EXCEL AYARLARI ---
def load_config():
    path = get_real_path("ayarlar.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(filepath):
    try:
        with open(get_real_path("ayarlar.json"), "w") as f:
            json.dump({"last_file": filepath}, f)
    except:
        pass

def get_excel_file():
    root = tk.Tk()
    root.withdraw()
    config = load_config()
    initial_dir = os.path.dirname(config.get("last_file", "")) if config.get("last_file") else "/"
    
    file_path = filedialog.askopenfilename(
        title="Veri Dosyasını Seçin",
        initialdir=initial_dir,
        filetypes=[("Excel Dosyaları", "*.xlsx;*.xls")]
    )
    if file_path:
        save_config(file_path)
        
    root.destroy()
    return file_path

# --- ANA İŞLEM ---
def main():
    file_path = get_excel_file()
    if not file_path:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Uyarı", "Dosya seçilmedi, program kapatılıyor.")
        root.destroy()
        sys.exit()

    try:
        df_raw = pd.read_excel(file_path)
        required_cols = {
            'Tarih': 'Tarih',
            'Model': 'Model',
            'Danışman Adı': 'Danışman Adı',
            'Durum': 'Durum',
            'Kayıp Nedeni': 'Kayıp Nedeni',
            'Lead Kaynağı': 'Lead Kaynağı'
        }
        df = pd.DataFrame()

        for col_code, col_excel in required_cols.items():
            if col_excel in df_raw.columns:
                df[col_code] = df_raw[col_excel].astype(str)
            else:
                found = False
                for raw_col in df_raw.columns:
                    if raw_col.strip() == col_excel:
                        df[col_code] = df_raw[raw_col].astype(str)
                        found = True
                        break
                if not found:
                    df[col_code] = 'Belirtilmemiş'
        
        df = df.replace(['nan', 'None', '', 'NaT'], 'Belirtilmemiş')
        json_data = df.to_json(orient='records')

        template_path = resource_path("tasarim.html")
        
        if not os.path.exists(template_path):
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Kritik Dosya Eksik!", f"Program çalışmak için 'tasarim.html' dosyasına ihtiyaç duyuyor ancak bulamadı.")
            root.destroy()
            sys.exit()

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        html_content = html_content.replace("[[JSON_DATA]]", json_data)
        html_content = html_content.replace("[[LOGO_SRC]]", get_image_data("logo.webp"))
        html_content = html_content.replace("[[GRAFIK_SRC]]", get_image_data("grafik_resmi.png"))
        html_content = html_content.replace("[[SIM_SRC]]", get_image_data("simulasyon_resmi.png"))

        # --- ÇÖZÜM: HER SEFERİNDE BENZERSİZ DOSYA ADI (CACHE KIRICI) ---
        temp_dir = tempfile.gettempdir()
        unique_id = uuid.uuid4().hex # Rastgele şifre üretir
        temp_file = os.path.join(temp_dir, f"SatisAnaliz_Temp_{unique_id}.html")

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        api = Api()
        webview.create_window('Satış Analiz Paneli', url=temp_file, js_api=api, width=1280, height=800)
        webview.start()

    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Hata", f"Beklenmeyen bir hata oluştu:\n{str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()
