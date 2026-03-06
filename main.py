import pandas as pd
import json
import os
import webbrowser
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil

# --- DOSYA SEÇME MEKANİZMASI ---
def get_excel_file():
    # 1. Önce yanımızda var mı bakalım (Kolaylık olsun diye)
    if os.path.exists("veri.xlsx"):
        return "veri.xlsx"
    
    # 2. Yoksa kullanıcıya soralım
    root = tk.Tk()
    root.withdraw() # Ana pencereyi gizle
    
    # Kullanıcıya bilgi verelim
    messagebox.showinfo("Veri Dosyası Gerekli", "Programın çalışması için satış verilerinin olduğu Excel dosyasını seçmeniz gerekiyor.")
    
    file_path = filedialog.askopenfilename(
        title="Lütfen veri.xlsx dosyasını seçin",
        filetypes=[("Excel Dosyaları", "*.xlsx;*.xls")]
    )
    
    if file_path:
        # Seçilen dosyayı programın yanına 'veri.xlsx' olarak kopyalayalım ki
        # bir dahaki sefere tekrar sormasın (İstersen bu satırı silebilirsin)
        try:
            shutil.copy(file_path, "veri.xlsx")
            return "veri.xlsx"
        except:
            return file_path # Kopyalayamazsa olduğu yerden okusun
    else:
        return None

# --- HTML ŞABLONU ---
html_content_start = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Yönetim Paneli - Güvenli Mod</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        body { background-color: #0e1117; color: white; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        .chart-box { background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; height: 400px; }
        .kpi-container { display: flex; gap: 20px; margin-bottom: 20px; }
        .kpi-card { background: #1e1e1e; flex: 1; padding: 20px; border-radius: 10px; text-align: center; border-top: 4px solid #00d4ff; font-size: 1.2rem; font-weight: bold; }
        h2 { color: #00d4ff; text-align: center; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .footer { text-align: center; margin-top: 20px; color: #555; font-size: 0.8rem; }
    </style>
</head>
<body>
    <h2>🚀 GÜVENLİ SATIŞ ANALİZ PANELİ</h2>
"""

html_content_end = """
    <div class="kpi-container">
        <div class="kpi-card" style="border-color: #3498db;">Toplam Görüşme: <br><span id="kpi-total">0</span></div>
        <div class="kpi-card" style="border-color: #2ecc71;">Toplam Satış: <br><span id="kpi-sales">0</span></div>
        <div class="kpi-card" style="border-color: #f1c40f;">Başarı Oranı: <br><span id="kpi-rate">%0</span></div>
    </div>

    <div class="grid">
        <div class="chart-box" id="c-durum"></div>
        <div class="chart-box" id="c-model"></div>
        <div class="chart-box" id="c-kayip"></div>
        <div class="chart-box" id="c-lead"></div>
    </div>
    
    <div class="footer">Bu rapor yerel dosyanızdan oluşturulmuştur. Verileriniz internete yüklenmemiştir.</div>

    <script>
        let rawData = JSON_DATA_HERE;

        function count(data, key) { 
            const c = {}; 
            data.forEach(d => c[d[key]] = (c[d[key]] || 0) + 1); 
            return c; 
        }

        function render() {
            if (rawData.length === 0) return;

            const total = rawData.length;
            const sales = rawData.filter(d => d.Durum === 'Satış').length;
            const rate = total > 0 ? ((sales/total)*100).toFixed(1) : 0;

            document.getElementById('kpi-total').innerText = total;
            document.getElementById('kpi-sales').innerText = sales;
            document.getElementById('kpi-rate').innerText = '%' + rate;

            const layout = { paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)', font:{color:'white'}, margin:{t:30,b:30,l:30,r:30} };
            
            // 1. Durum Pasta
            const d1 = count(rawData, "Durum");
            Plotly.newPlot('c-durum', [{ values: Object.values(d1), labels: Object.keys(d1), type: 'pie', hole: 0.4 }], { ...layout, title: 'Satış Durumu' });

            // 2. Model Bar
            const models = count(rawData.filter(d=>d.Durum==='Satış'), 'Model');
            Plotly.newPlot('c-model', [{ x: Object.values(models), y: Object.keys(models), type: 'bar', orientation: 'h', marker:{color:'#2ecc71'} }], { ...layout, title: 'Satılan Modeller' });

            // 3. Kayıp
            const losses = count(rawData.filter(d=>d.Durum!=='Satış'), 'Kayıp Nedeni');
            Plotly.newPlot('c-kayip', [{ x: Object.keys(losses), y: Object.values(losses), type: 'bar', marker:{color:'#e74c3c'} }], { ...layout, title: 'Kayıp Nedenleri' });

            // 4. Lead (DÜZELTİLDİ: Lead Kaynağı sütunu)
            const sources = count(rawData, 'Lead Kaynağı');
            Plotly.newPlot('c-lead', [{ x: Object.keys(sources), y: Object.values(sources), type: 'bar', marker:{color:'#9b59b6'} }], { ...layout, title: 'Müşteri Kaynağı' });
        }

        render();
    </script>
</body>
</html>
"""

def main():
    target_file = get_excel_file()
    
    if not target_file:
        print("Dosya seçilmedi. Program kapatılıyor.")
        return

    try:
        # Excel Okuma
        df = pd.read_excel(target_file)
        
        # Sütun Eşleştirme (Senin Excel yapına göre)
        column_map = {
            'Danışman Adı': 'Danışman Adı', 
            'Model': 'Model', 
            'Durum': 'Durum',
            'Kapatılma Tarihi': 'Tarih', 
            'Kayıp Satış Nedeni': 'Kayıp Nedeni',
            'Lead Kaynağı': 'Lead Kaynağı' # Burası kritik
        }
        
        df_clean = pd.DataFrame()
        for col_excel, col_code in column_map.items():
            if col_excel in df.columns:
                df_clean[col_code] = df[col_excel].astype(str).replace(['nan', 'None', '', 'NaT'], 'Belirtilmemiş')
            else:
                df_clean[col_code] = 'Belirtilmemiş'
        
        json_str = df_clean.to_json(orient='records')
        
        # HTML Oluştur
        final_html = html_content_start.replace("JSON_DATA_HERE", json_str) + html_content_end
        
        with open("Rapor_Paneli.html", "w", encoding="utf-8") as f:
            f.write(final_html)
        
        print("Panel hazır! Tarayıcı açılıyor...")
        webbrowser.open("Rapor_Paneli.html")
        
    except Exception as e:
        # Hata olursa pencere açıp gösterelim
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Hata Oluştu", f"Excel dosyası okunurken hata oluştu:\n{str(e)}")

if __name__ == "__main__":
    main()
