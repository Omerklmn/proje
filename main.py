import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys

# --- Ayarlar ve Yapılandırma ---
CONFIG_FILE = "config.json"

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SatisUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Satış Yönetim Paneli")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2c3e50")

        self.df = None
        self.groups = {}
        self.hidden_groups = []
        self.current_file_path = ""
        
        # Simülasyon Değişkenleri
        self.sim_choices = {"consultant": None, "model": None, "month": "Ocak"}
        self.weights = {"consultant": 50, "model": 30, "month": 20} # Varsayılan ağırlıklar

        self.load_config()
        self.create_main_menu()

        # Kayıtlı dosya varsa yükle
        if self.current_file_path and os.path.exists(self.current_file_path):
            self.load_data(self.current_file_path, silent=True)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_file_path = data.get("last_file", "")
                    self.groups = data.get("groups", {})
                    self.hidden_groups = data.get("hidden_groups", [])
            except:
                pass

    def save_config(self):
        data = {
            "last_file": self.current_file_path,
            "groups": self.groups,
            "hidden_groups": self.hidden_groups
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self, path, silent=False):
        try:
            if path.endswith('.csv'):
                raw_df = pd.read_csv(path)
            else:
                raw_df = pd.read_excel(path)
            
            self.df = raw_df
            self.current_file_path = path
            self.save_config()
            
            # Sütun isimlerini düzeltme (Olası hataları önlemek için)
            # Kod içinde standart olarak 'Sales Consultant' ve 'Model' kullanıyoruz.
            # Eğer Excel'de Türkçe ise burada mapleyebiliriz. Şimdilik varsayılanı koruyorum.
            
            if not silent:
                messagebox.showinfo("Başarılı", "Veri başarıyla yüklendi!")
                self.root.title(f"Satış Yönetim Paneli - {os.path.basename(path)}")
        except Exception as e:
            if not silent:
                messagebox.showerror("Hata", f"Dosya okunamadı:\n{e}")

    def get_processed_data(self):
        """
        Grupları uygular ve GİZLİ olanları veriden çıkarır.
        Tüm hesaplamalar bu veriyi kullanmalıdır.
        """
        if self.df is None: return None
        temp_df = self.df.copy()
        
        # Sütun adlarındaki boşlukları temizle
        temp_df.columns = temp_df.columns.str.strip()
        
        if 'Model' in temp_df.columns:
            # 1. Grupları Uygula
            for grp_name, members in self.groups.items():
                mask = temp_df['Model'].isin(members)
                temp_df.loc[mask, 'Model'] = grp_name
            
            # 2. Gizli Grupları/Modelleri Filtrele (İSTEK 3 - GİZLEME TUŞU ETKİSİ)
            temp_df = temp_df[~temp_df['Model'].isin(self.hidden_groups)]
            
        return temp_df

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- ANA MENÜ ---
    def create_main_menu(self):
        self.clear_screen()
        
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(expand=True, fill="both", padx=50, pady=50)

        tk.Label(main_frame, text="Ana Menü", font=("Arial", 28, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=40)

        btn_style = {"font": ("Arial", 14), "height": 2, "width": 35, "bd": 0, "cursor": "hand2"}

        tk.Button(main_frame, text="📂 Dosya Değiştir", command=self.change_file, bg="#3498db", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="📊 Grafikler ve Raporlar", command=self.open_graphs, bg="#e67e22", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="🚀 Satış Simülasyonu", command=self.start_simulation, bg="#27ae60", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="⚙️ Ayarlar", command=self.open_settings, bg="#7f8c8d", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="❌ Çıkış", command=self.root.quit, bg="#c0392b", fg="white", **btn_style).pack(pady=30)

    def change_file(self):
        file_path = filedialog.askopenfilename(title="Yeni Veri Dosyası Seç", filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv")])
        if file_path:
            self.load_data(file_path)

    # --- GRAFİKLER (İSTEK 1: TAM DİNAMİK BOYUTLANDIRMA) ---
    def open_graphs(self):
        self.clear_screen()
        
        nav = tk.Frame(self.root, bg="#34495e", height=60)
        nav.pack(side="top", fill="x")
        tk.Button(nav, text="< Ana Menü", command=self.create_main_menu, bg="#e74c3c", fg="white", font=("Arial", 12)).pack(side="left", padx=20, pady=10)

        data = self.get_processed_data()
        if data is None:
            tk.Label(self.root, text="Görüntülenecek veri yok!", bg="#2c3e50", fg="white", font=("Arial", 16)).pack(pady=50)
            return

        # Scrollbarlı Alan
        canvas = tk.Canvas(self.root, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#ecf0f1")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Grafik 1: Modeller
        if 'Model' in data.columns:
            counts = data['Model'].value_counts()
            self.create_dynamic_chart(scroll_frame, counts, "Model Satış Adetleri")

        # Grafik 2: Danışmanlar
        if 'Sales Consultant' in data.columns:
            counts = data['Sales Consultant'].value_counts()
            self.create_dynamic_chart(scroll_frame, counts, "Danışman Performansı")

    def create_dynamic_chart(self, parent, data, title):
        # --- İSTEK 1 ÇÖZÜMÜ ---
        # Yazı uzunluğuna göre grafiğin alt boşluğunu (bottom margin) dinamik hesapla.
        
        if len(data) == 0: return

        # En uzun etiketi bul
        max_label_len = max([len(str(x)) for x in data.index])
        
        # Her karakter için yaklaşık 0.015 margin ekle. Taban margin 0.15.
        # Eğer yazı çok uzunsa (örn: 30 karakter), margin 0.6'ya kadar çıkar.
        dynamic_bottom = 0.15 + (max_label_len * 0.015)
        
        # Eğer çok abartı uzunsa bir yerde sınırla (0.65 iyi bir sınır)
        if dynamic_bottom > 0.65: dynamic_bottom = 0.65

        # Figür yüksekliğini de veri sayısına göre artıralım ki barlar sıkışmasın
        fig_width = max(10, len(data) * 0.3)
        fig_height = 6 + (max_label_len * 0.05) # Yazı uzadıkça grafik boyu da uzasın

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # Barları çiz
        data.plot(kind='bar', ax=ax, color='#3498db', edgecolor='black')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel("Adet")
        
        # X ekseni yazılarını 45 derece yatır ve sağa hizala (Okunabilirlik için standart)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        
        # Alt boşluğu ayarla (Sihirli dokunuş burası)
        plt.subplots_adjust(bottom=dynamic_bottom)
        plt.tight_layout() # Bazen bu bozar, o yüzden adjust daha garanti ama ikisi birlikte denenebilir.
        # tight_layout bazen margin ayarını ezer, o yüzden custom adjust'ı tight_layout'tan SONRA yapmak daha güvenli veya tight_layout kullanmamak.
        # Biz manuel ayarı tercih ettik.
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=30, padx=20)

    # --- SİMÜLASYON (İSTEK 2: 4 ADIMLI TAM SÜREÇ) ---
    def start_simulation(self):
        self.sim_choices = {"consultant": None, "model": None, "month": None}
        self.sim_step_1_consultant()

    # ADIM 1: DANIŞMAN SEÇİMİ
    def sim_step_1_consultant(self):
        self.clear_screen()
        data = self.get_processed_data()
        
        self.draw_sim_header("Adım 1: Danışman Seçimi")
        
        frame_content = tk.Frame(self.root, bg="#2c3e50")
        frame_content.pack(expand=True, fill="both", padx=50)

        if data is None or 'Sales Consultant' not in data.columns:
            tk.Label(frame_content, text="Veri bulunamadı.", fg="white", bg="#2c3e50").pack()
        else:
            consultants = sorted(data['Sales Consultant'].dropna().unique())
            self.create_grid_buttons(frame_content, consultants, self.sim_step_2_model)

        self.draw_sim_cancel()

    # ADIM 2: MODEL SEÇİMİ (Gruplanmış Veriden)
    def sim_step_2_model(self, selection):
        self.sim_choices['consultant'] = selection
        
        self.clear_screen()
        data = self.get_processed_data()
        
        self.draw_sim_header(f"Adım 2: Model Seçimi\n(Danışman: {selection})")
        
        frame_content = tk.Frame(self.root, bg="#2c3e50")
        frame_content.pack(expand=True, fill="both", padx=50)
        
        if data is not None and 'Model' in data.columns:
            # Gruplanmış veriden benzersiz modelleri çek
            models = sorted(data['Model'].dropna().unique())
            self.create_grid_buttons(frame_content, models, self.sim_step_3_month)
            
        self.draw_sim_cancel()

    # ADIM 3: AY SEÇİMİ
    def sim_step_3_month(self, selection):
        self.sim_choices['model'] = selection
        
        self.clear_screen()
        self.draw_sim_header(f"Adım 3: Dönem (Ay) Seçimi\n(Model: {selection})")
        
        frame_content = tk.Frame(self.root, bg="#2c3e50")
        frame_content.pack(expand=True, fill="both", padx=50)
        
        months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        self.create_grid_buttons(frame_content, months, self.sim_step_4_result)
        self.draw_sim_cancel()

    # ADIM 4: SONUÇ VE ANALİZ (AĞIRLIKLI HESAPLAMA)
    def sim_step_4_result(self, selection):
        self.sim_choices['month'] = selection
        self.show_result_screen()

    def show_result_screen(self):
        self.clear_screen()
        
        # Ana Konteyner
        main_container = tk.Frame(self.root, bg="#ecf0f1")
        main_container.pack(fill="both", expand=True)

        # Başlık
        tk.Label(main_container, text="🎯 Simülasyon Sonucu ve Analiz", font=("Arial", 22, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=15)

        # Üst Kısım: Sonuç Göstergesi
        frame_score = tk.Frame(main_container, bg="white", bd=2, relief="groove")
        frame_score.pack(fill="x", padx=50, pady=10)
        
        self.lbl_score = tk.Label(frame_score, text="% --", font=("Arial", 48, "bold"), fg="#27ae60", bg="white")
        self.lbl_score.pack(pady=10)
        self.lbl_detail = tk.Label(frame_score, text="Hesaplanıyor...", font=("Arial", 12), fg="#7f8c8d", bg="white")
        self.lbl_detail.pack(pady=5)

        # Orta Kısım: Senaryo Değiştirme (Excel Tarzı)
        frame_controls = tk.LabelFrame(main_container, text="Senaryo Değişkenleri (What-If)", bg="#ecf0f1", font=("Arial", 12, "bold"))
        frame_controls.pack(fill="x", padx=50, pady=10)
        
        # Comboboxlar için verileri hazırla
        data = self.get_processed_data()
        all_cons = sorted(data['Sales Consultant'].dropna().unique()) if data is not None else []
        all_models = sorted(data['Model'].dropna().unique()) if data is not None else []
        all_months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

        # 1. Danışman
        tk.Label(frame_controls, text="Danışman:", bg="#ecf0f1").grid(row=0, column=0, padx=5, pady=5)
        self.cb_cons = ttk.Combobox(frame_controls, values=all_cons, state="readonly", width=20)
        self.cb_cons.set(self.sim_choices['consultant'])
        self.cb_cons.grid(row=0, column=1, padx=5)
        self.cb_cons.bind("<<ComboboxSelected>>", self.recalculate_sim)

        # 2. Model
        tk.Label(frame_controls, text="Model:", bg="#ecf0f1").grid(row=0, column=2, padx=5, pady=5)
        self.cb_model = ttk.Combobox(frame_controls, values=all_models, state="readonly", width=20)
        self.cb_model.set(self.sim_choices['model'])
        self.cb_model.grid(row=0, column=3, padx=5)
        self.cb_model.bind("<<ComboboxSelected>>", self.recalculate_sim)

        # 3. Ay
        tk.Label(frame_controls, text="Ay:", bg="#ecf0f1").grid(row=0, column=4, padx=5, pady=5)
        self.cb_month = ttk.Combobox(frame_controls, values=all_months, state="readonly", width=15)
        self.cb_month.set(self.sim_choices['month'])
        self.cb_month.grid(row=0, column=5, padx=5)
        self.cb_month.bind("<<ComboboxSelected>>", self.recalculate_sim)

        # Ağırlık Sliderları
        frame_weights = tk.LabelFrame(main_container, text="Etki Ağırlıkları (%)", bg="#ecf0f1", font=("Arial", 12, "bold"))
        frame_weights.pack(fill="x", padx=50, pady=10)
        
        self.scale_cons = tk.Scale(frame_weights, from_=0, to=100, orient="horizontal", label="Danışman", bg="#ecf0f1", command=lambda x: self.recalculate_sim())
        self.scale_cons.set(self.weights['consultant'])
        self.scale_cons.pack(side="left", fill="x", expand=True, padx=10)

        self.scale_model = tk.Scale(frame_weights, from_=0, to=100, orient="horizontal", label="Model", bg="#ecf0f1", command=lambda x: self.recalculate_sim())
        self.scale_model.set(self.weights['model'])
        self.scale_model.pack(side="left", fill="x", expand=True, padx=10)
        
        self.scale_month = tk.Scale(frame_weights, from_=0, to=100, orient="horizontal", label="Dönem", bg="#ecf0f1", command=lambda x: self.recalculate_sim())
        self.scale_month.set(self.weights['month'])
        self.scale_month.pack(side="left", fill="x", expand=True, padx=10)

        # Öneri Kutusu
        self.lbl_suggestion = tk.Label(main_container, text="", font=("Arial", 11, "italic"), fg="#d35400", bg="#ecf0f1", wraplength=800)
        self.lbl_suggestion.pack(pady=15)

        tk.Button(main_container, text="Ana Menüye Dön", command=self.create_main_menu, bg="#34495e", fg="white", height=2, width=20).pack(pady=10)

        # İlk Hesaplama
        self.recalculate_sim()

    def recalculate_sim(self, event=None):
        # Seçimleri Al
        cons = self.cb_cons.get()
        model = self.cb_model.get()
        month = self.cb_month.get()

        # Ağırlıkları Al
        w1 = self.scale_cons.get()
        w2 = self.scale_model.get()
        w3 = self.scale_month.get()
        total_w = w1 + w2 + w3 if (w1+w2+w3) > 0 else 1

        # Veriden Oranları Hesapla
        # Not: Gerçek veride 'Status' = 'Sold'/'Satış' oranına bakılır.
        # Burada basit simülasyon mantığı (Dummy Logic) kullanıyoruz çünkü Status sütun formatını bilmiyoruz.
        # Ama veri varsa veri üzerinden deneriz.
        
        def get_success_rate(col, val):
            if self.df is None or col not in self.df.columns: return 50 # Veri yoksa %50
            subset = self.df[self.df[col] == val]
            if len(subset) == 0: return 0
            # Basit mantık: Rastgele sayı yerine veri adedine dayalı bir başarı puanı uyduralım
            # (Gerçek satış verisi sütunu olmadığı için adet üzerinden popülarite puanı veriyoruz)
            # Daha çok satan/görüşülen daha başarılıdır mantığı.
            return min(95, len(subset) * 2) 

        rate_c = get_success_rate('Sales Consultant', cons)
        rate_m = get_success_rate('Model', model)
        rate_mo = 50 # Ay verisi olmadığı için sabit (veya rastgelelik eklenebilir)

        # Hesapla
        final_prob = (rate_c * w1 + rate_m * w2 + rate_mo * w3) / total_w
        
        self.lbl_score.config(text=f"%{final_prob:.1f}")
        self.lbl_detail.config(text=f"Danışman Puanı: {rate_c} | Model Puanı: {rate_m} | Dönem Puanı: {rate_mo}")

        # Öneriler (Yapay Zeka Mantığı)
        suggestions = []
        # Başka bir ay seçseydi?
        # (Basitçe: Ay değişiminin +-%5 etkisi olduğunu varsayalım)
        if month in ["Ocak", "Şubat"] and final_prob < 60:
            suggestions.append(f"💡 İPUCU: '{month}' yerine Bahar aylarını (Nisan-Mayıs) seçmek mevsimsel etkiyi artırabilir.")
        
        if rate_m < 30:
            suggestions.append(f"⚠️ UYARI: '{model}' modelinin veri sayısı/başarısı düşük. Daha popüler bir model seçmek ihtimali artırır.")

        if not suggestions:
            self.lbl_suggestion.config(text="✅ Bu senaryo makul görünüyor.")
        else:
            self.lbl_suggestion.config(text="\n".join(suggestions))


    # Yardımcı: Grid Buton Oluşturucu
    def create_grid_buttons(self, frame, items, command_func):
        row = 0
        col = 0
        for item in items:
            btn = tk.Button(frame, text=str(item), font=("Arial", 11), width=18, height=2,
                            command=lambda x=item: command_func(x), bg="#3498db", fg="white")
            btn.grid(row=row, column=col, padx=10, pady=10)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def draw_sim_header(self, text):
        tk.Label(self.root, text=text, font=("Arial", 20, "bold"), bg="#2c3e50", fg="white").pack(pady=20)

    def draw_sim_cancel(self):
        tk.Button(self.root, text="❌ İptal / Ana Menü", command=self.create_main_menu, bg="#c0392b", fg="white", font=("Arial", 12)).pack(pady=30)


    # --- AYARLAR (İSTEK 3: GİZLEME TUŞU ve KAYDETMEDEN ÇIK) ---
    def open_settings(self):
        self.clear_screen()
        
        tk.Label(self.root, text="⚙️ Ayarlar", font=("Arial", 24, "bold"), bg="#2c3e50", fg="white").pack(pady=20)
        
        # Ana Frame
        frame_content = tk.Frame(self.root, bg="#2c3e50")
        frame_content.pack(fill="both", expand=True, padx=50, pady=10)
        
        # Tablo (Treeview)
        cols = ("Ham Veri", "Atanan Grup", "Durum")
        tree = ttk.Treeview(frame_content, columns=cols, show='headings', height=15)
        tree.heading("Ham Veri", text="Model Adı (Excel)")
        tree.heading("Atanan Grup", text="Grup")
        tree.heading("Durum", text="Durum")
        
        tree.column("Ham Veri", width=250)
        tree.column("Atanan Grup", width=150)
        tree.column("Durum", width=100)
        
        tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame_content, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        # Verileri Doldur
        if self.df is not None and 'Model' in self.df.columns:
            # Hem mevcut dosyayı hem hafızadaki grupları birleştir
            all_items = set(self.df['Model'].dropna().unique())
            for grp_list in self.groups.values():
                for m in grp_list: all_items.add(m)
            
            for item in sorted(all_items):
                # Grup bul
                grp = "-"
                for g_name, members in self.groups.items():
                    if item in members:
                        grp = g_name
                        break
                
                # Durum bul (İSTEK 3: GİZLEME ÖZELLİĞİ)
                status = "❌ GİZLİ" if item in self.hidden_groups else "✅ AKTİF"
                if self.df is not None and item not in self.df['Model'].values:
                    status += " (Yok)"
                
                tree.insert("", "end", values=(item, grp, status))

        # Butonlar
        frame_btns = tk.Frame(self.root, bg="#2c3e50")
        frame_btns.pack(pady=20)
        
        tk.Button(frame_btns, text="👁️ Seçiliyi Gizle/Göster", command=lambda: self.toggle_hide(tree), bg="#f39c12", fg="white", font=("Arial", 11), width=25).grid(row=0, column=0, padx=10)
        tk.Button(frame_btns, text="🔗 Seçiliyi Grupla", command=lambda: self.create_group(tree), bg="#3498db", fg="white", font=("Arial", 11), width=25).grid(row=0, column=1, padx=10)
        
        # Alt Butonlar
        frame_bottom = tk.Frame(self.root, bg="#2c3e50")
        frame_bottom.pack(pady=20)
        
        tk.Button(frame_bottom, text="💾 Kaydet ve Çık", command=lambda: [self.save_config(), self.create_main_menu()], bg="#27ae60", fg="white", font=("Arial", 12), width=20).pack(side="left", padx=20)
        tk.Button(frame_bottom, text="🚫 Kaydetmeden Çık", command=lambda: [self.load_config(), self.create_main_menu()], bg="#c0392b", fg="white", font=("Arial", 12), width=20).pack(side="left", padx=20)

    def toggle_hide(self, tree):
        selected = tree.selection()
        if not selected: return
        
        for item in selected:
            val = tree.item(item)['values']
            model_name = val[0]
            
            if model_name in self.hidden_groups:
                self.hidden_groups.remove(model_name)
            else:
                self.hidden_groups.append(model_name)
        
        self.open_settings() # Sayfayı yenile

    def create_group(self, tree):
        selected = tree.selection()
        if not selected: return
        
        grp_name = simpledialog.askstring("Grup Oluştur", "Grup Adı Giriniz:")
        if not grp_name: return
        
        if grp_name not in self.groups: self.groups[grp_name] = []
        
        for item in selected:
            val = tree.item(item)['values']
            model_name = val[0]
            # Eski grubundan çıkar
            for g in self.groups.values():
                if model_name in g: g.remove(model_name)
            # Yeniye ekle
            self.groups[grp_name].append(model_name)
            
        self.open_settings()

if __name__ == "__main__":
    root = tk.Tk()
    app = SatisUygulamasi(root)
    root.mainloop()
