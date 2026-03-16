import pandas as pd
import json
import os
import sys
import base64
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import webview
import tempfile
import uuid

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

class Api:
    def __init__(self, veri_json):
        self.veri_json = veri_json

    def get_excel_veri(self):
        return self.veri_json

    def save_ui_settings(self, settings_json):
        try:
            path = get_real_path("ui_ayarlar.json")
            with open(path, "w", encoding="utf-8") as f:
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
            except Exception:
                return "{}"
        return "{}"

def get_excel_file():
    root = tk.Tk()
    root.withdraw()
    
    config_path = get_real_path("ayarlar.json")
    last_file = ""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                last_file = config.get("last_file", "")
        except:
            pass
            
    if last_file and os.path.exists(last_file):
        filename = os.path.basename(last_file)
        cevap = messagebox.askyesno("Kayıtlı Veri Bulundu", f"Önceki analizde şu dosya kullanılmış:\n\n{filename}\n\nBu dosya ile devam edilsin mi?\n(Farklı bir Excel seçmek için Hayır'a tıklayın)")
        if cevap:
            root.destroy()
            return last_file
            
    initial_dir = os.path.dirname(last_file) if last_file else "/"
    file_path = filedialog.askopenfilename(
        title="Veri Dosyasını Seçin",
        initialdir=initial_dir,
        filetypes=[("Excel Dosyaları", "*.xlsx;*.xls")]
    )
    
    if file_path:
        try:
            with open(config_path, "w") as f:
                json.dump({"last_file": file_path}, f)
        except:
            pass
            
    root.destroy()
    return file_path

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
        
        df = df.fillna('Belirtilmemiş')
        df = df.replace(['nan', 'None', '', 'NaT', 'null'], 'Belirtilmemiş')
        json_data = df.to_json(orient='records')

        template_path = resource_path("tasarim.html")
        if not os.path.exists(template_path):
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Hata", "tasarim.html bulunamadı!")
            root.destroy()
            sys.exit()

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Resimleri gömüyoruz
        html_content = html_content.replace("[[LOGO_SRC]]", get_image_data("logo.webp"))
        html_content = html_content.replace("[[GRAFIK_SRC]]", get_image_data("grafik_resmi.png"))
        html_content = html_content.replace("[[SIM_SRC]]", get_image_data("simulasyon_resmi.png"))

        gercek_klasor = get_real_path("")
        
        try:
            for dosya_adi in os.listdir(gercek_klasor):
                if dosya_adi.startswith("SatisAnaliz_Gizli_") and dosya_adi.endswith(".html"):
                    try:
                        os.remove(os.path.join(gercek_klasor, dosya_adi))
                    except:
                        pass
        except:
            pass

        unique_id = uuid.uuid4().hex
        temp_file = os.path.join(gercek_klasor, f"SatisAnaliz_Gizli_{unique_id}.html")

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        api = Api(json_data)
        window = webview.create_window('Satış Analiz Paneli', url=temp_file, js_api=api, width=1280, height=800)

        # PYTHON EKRANIN YÜKLENMESİNİ BEKLER
        def on_loaded():
            time.sleep(0.3) # JS'nin DOM'u hazırlaması için milisaniyelik bir esneklik payı
            excel_b64 = base64.b64encode(api.veri_json.encode('utf-8')).decode('utf-8')
            ayarlar_b64 = base64.b64encode(api.load_ui_settings().encode('utf-8')).decode('utf-8')
            window.evaluate_js(f"sistemiBaslat('{excel_b64}', '{ayarlar_b64}');")

        window.events.loaded += on_loaded
        webview.start()

    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Hata", f"Beklenmeyen bir hata:\n{str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()
