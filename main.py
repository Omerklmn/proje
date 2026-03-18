import pandas as pd
import json
import os
import sys
import base64
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_image_data(filename):
    path = resource_path(filename)
    if not os.path.exists(path):
        path = filename
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                ext = filename.split(".")[-1].lower()
                mime = "image/webp" if ext == "webp" else "image/png"
                return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
        except:
            pass
    return ""

CONFIG_FILE = "ayarlar.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
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
    if not target_file:
        return

    try:
        df_raw = pd.read_excel(target_file)

        # Sütun eşleştirme - Excel başlığı : kod değişkeni
        column_map = {
            'Danışman Adı':         'Danışman Adı',
            'Model':                'Model',
            'Durum':                'Durum',
            'Kapatılma Tarihi':     'Tarih',
            'Kayıp Satış Nedeni':   'Kayıp Nedeni',
            'Lead Kaynağı':         'Lead Kaynağı',
            'Lead No':              'Lead No',
            'Kayıt Adı':            'Kayıt Adı',
            'Kayıt Telefon No':     'Kayıt Telefon No',
        }

        df = pd.DataFrame()
        for col_excel, col_code in column_map.items():
            if col_excel in df_raw.columns:
                df[col_code] = df_raw[col_excel].astype(str)
            else:
                matched = next((c for c in df_raw.columns if c.strip() == col_excel), None)
                df[col_code] = df_raw[matched].astype(str) if matched else 'Belirtilmemiş'

        df = df.replace(['nan', 'None', '', 'NaT'], 'Belirtilmemiş')

        # Ham model listesi (gruplandırılmamış) - stok kartı için
        raw_models = sorted(df['Model'].dropna().unique().tolist())
        raw_models = [m for m in raw_models if m != 'Belirtilmemiş']

        json_data = df.to_json(orient='records', force_ascii=False)

        template_path = resource_path("tasarim.html")
        if not os.path.exists(template_path):
            template_path = "tasarim.html"

        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        html = html.replace("[[JSON_DATA]]", json_data)
        html = html.replace("[[RAW_MODELS]]", json.dumps(raw_models, ensure_ascii=False))
        html = html.replace("[[LOGO_SRC]]", get_image_data("logo.webp"))
        html = html.replace("[[GRAFIK_SRC]]", get_image_data("grafik_resmi.png"))
        html = html.replace("[[SIM_SRC]]", get_image_data("simulasyon_resmi.png"))

        with open("Satis_Raporu.html", "w", encoding="utf-8") as f:
            f.write(html)

        webbrowser.open("Satis_Raporu.html")

    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Hata", str(e))

if __name__ == "__main__":
    main()
