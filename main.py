import pandas as pd
import json
import os
import sys
import base64
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

# --- YARDIMCI FONKSİYONLAR ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

# --- AYARLAR ---
CONFIG_FILE = "ayarlar.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(path):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"last_file": path}, f)
    except:
        pass

def get_excel_file():
    root = tk.Tk()
    root.withdraw()
    config = load_config()
    last_file = config.get("last_file")

    if last_file and os.path.exists(last_file):
        if messagebox.askyesno("Dosya", f"Son dosya ile devam?\n{last_file}"):
            return last_file
            
    file_path = filedialog.askopenfilename(title="Excel Seç", filetypes=[("Excel", "*.xlsx;*.xls")])
    if file_path:
        save_config(file_path)
        return file_path
    return None

def main():
    target_file = get_excel_file()
    if not target_file: return

    try:
        # Excel Okuma ve Temizleme
        df_raw = pd.read_excel(target_file)
        df = pd.DataFrame()
        
        # Sütun Eşleştirme (Excel'deki isim ne olursa olsun koda uydur)
        column_map = {
            'Danışman Adı': 'Danışman Adı',
            'Model': 'Model',
            'Durum': 'Durum',
            'Kapatılma Tarihi': 'Tarih',
            'Kayıp Satış Nedeni': 'Kayıp Nedeni',
            'Lead Kaynağı': 'Lead Kaynağı'
        }
        
        for col_excel, col_code in column_map.items():
            # Tam eşleşme ara, yoksa sütun adlarını temizleyip ara
            if col_excel in df_raw.columns:
                df[col_code] = df_raw[col_excel].astype(str)
            else:
                # Esnek arama (boşlukları silip bak)
                found = False
                for raw_col in df_raw.columns:
                    if raw_col.strip() == col_excel:
                        df[col_code] = df_raw[raw_col].astype(str)
                        found = True
                        break
                if not found:
                    df[col_code] = 'Belirtilmemiş'
        
        # Temizlik
        df = df.replace(['nan', 'None', '', 'NaT'], 'Belirtilmemiş')
        json_data = df.to_json(orient='records')

        # HTML Hazırlığı
        template_path = resource_path("tasarim.html")
        if not os.path.exists(template_path): template_path = "tasarim.html"

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        html_content = html_content.replace("[[JSON_DATA]]", json_data)
        html_content = html_content.replace("[[LOGO_SRC]]", get_image_data("logo.webp"))
        html_content = html_content.replace("[[GRAFIK_SRC]]", get_image_data("grafik_resmi.png"))
        html_content = html_content.replace("[[SIM_SRC]]", get_image_data("simulasyon_resmi.png"))

        with open("Satis_Raporu.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        webbrowser.open("Satis_Raporu.html")

    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Hata", str(e))

if __name__ == "__main__":
    main()
