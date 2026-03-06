import pandas as pd
import json
import os
import sys
import base64
import webbrowser
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

# --- YARDIMCI FONKSİYONLAR ---

def resource_path(relative_path):
    """ Exe çalışırken ve normal çalışırken dosya yolunu bulur """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_image_data(filename):
    """ Resim dosyasını Base64 formatına çevirir """
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

# --- İSTEK 1: DOSYA HAFIZASI ---
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
    root.withdraw() # Pencereyi gizle

    config = load_config()
    last_file = config.get("last_file")

    # Eğer son dosya varsa sor
    if last_file and os.path.exists(last_file):
        msg = f"Son kullanılan dosya bulundu:\n{last_file}\n\nBu dosya ile devam etmek ister misiniz?\n('Hayır' derseniz yeni dosya seçebilirsiniz)"
        response = messagebox.askyesno("Dosya Seçimi", msg)
        if response:
            return last_file
    
    # Yoksa veya Hayır dendiyse yeni seçtir
    messagebox.showinfo("Dosya Seçimi", "Lütfen analiz edilecek Excel dosyasını seçin.")
    file_path = filedialog.askopenfilename(title="Excel Dosyası Seç", filetypes=[("Excel Dosyaları", "*.xlsx;*.xls")])
    
    if file_path:
        save_config(file_path) # Yeni seçimi kaydet
        return file_path
    
    return None

def main():
    # 1. Dosya Seçimi
    target_file = get_excel_file()
    
    if not target_file:
        return

    try:
        # 2. Excel Okuma
        df_raw = pd.read_excel(target_file)
        df = pd.DataFrame()
        
        column_map = {
            'Danışman Adı': 'Danışman Adı',
            'Model': 'Model',
            'Durum': 'Durum',
            'Kapatılma Tarihi': 'Tarih',
            'Kayıp Satış Nedeni': 'Kayıp Nedeni',
            'Lead Kaynağı': 'Lead Kaynağı'
        }
        
        for col_excel, col_code in column_map.items():
            if col_excel in df_raw.columns:
                df[col_code] = df_raw[col_excel].astype(str)
            else:
                for raw_col in df_raw.columns:
                    if raw_col.strip() == col_excel:
                        df[col_code] = df_raw[raw_col].astype(str)
                        break
                if col_code not in df:
                    df[col_code] = 'Belirtilmemiş'
        
        # NaN temizliği
        for col in df.columns:
            df[col] = df[col].replace(['nan', 'None', '', 'NaT', 'NaN'], 'Belirtilmemiş')
            
        json_data = df.to_json(orient='records')
        
        # 3. Resimleri Yükle
        logo_img = get_image_data("logo.webp") 
        grafik_img = get_image_data("grafik_resmi.png")
        sim_img = get_image_data("simulasyon_resmi.png")
        
        # 4. HTML Şablonunu Oku (Exe içinden veya yanından)
        template_path = resource_path("tasarim.html")
        if not os.path.exists(template_path):
            template_path = "tasarim.html"

        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        # 5. Verileri HTML'e Göm
        final_html = html_template.replace("[[JSON_DATA]]", json_data)
        final_html = final_html.replace("[[LOGO_SRC]]", logo_img)
        final_html = final_html.replace("[[GRAFIK_SRC]]", grafik_img)
        final_html = final_html.replace("[[SIM_SRC]]", sim_img)
        
        # 6. Çıktı Dosyası
        output_file = "Satis_Raporu.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)
        
        webbrowser.open(output_file)
        
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Hata", f"Beklenmedik bir hata oluştu:\n{e}")

if __name__ == "__main__":
    main()
