import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys

# --- Dosya Yolları ve Yapılandırma ---
CONFIG_FILE = "config.json"

def get_resource_path(relative_path):
    """PyInstaller ve geliştirme ortamı için dosya yolu bulucu."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Veri Yönetimi Sınıfı ---
class DataManager:
    def __init__(self):
        self.df = None
        self.raw_df = None  # Filtresiz ham veri
        self.file_path = ""
        self.groups = {} # { "GrupAdi": ["Model1", "Model2"], ... }
        self.hidden_groups = [] # ["GrupAdi1", "GrupAdi2"] - Gizlenen gruplar
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.file_path = data.get("last_file", "")
                    self.groups = data.get("groups", {})
                    self.hidden_groups = data.get("hidden_groups", [])
            except:
                pass

    def save_config(self):
        data = {
            "last_file": self.file_path,
            "groups": self.groups,
            "hidden_groups": self.hidden_groups
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self, path=None):
        if path:
            self.file_path = path
        
        if not self.file_path or not os.path.exists(self.file_path):
            return False

        try:
            if self.file_path.endswith('.csv'):
                self.raw_df = pd.read_csv(self.file_path)
            else:
                self.raw_df = pd.read_excel(self.file_path)
            
            # Veri Ön İşleme (Standartlaştırma)
            self.process_data()
            self.save_config()
            return True
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okunamadı:\n{e}")
            return False

    def process_data(self):
        """Gruplamaları ve Gizlemeleri Uygula"""
        if self.raw_df is None:
            return

        self.df = self.raw_df.copy()
        
        # Sütun isimlerini temizle
        self.df.columns = self.df.columns.str.strip()

        # Kritik Sütun Kontrolü (Örnek sütun isimleri - senin excel'ine göre buralar önemli)
        # Genelde: 'Model', 'Sales Consultant', 'Lead Source', 'Status' vb.
        # Biz burada varsayılan isimleri kullanacağız, yoksa hata almamak için kontrol edelim.
        
        # 1. Gruplama Mantığı
        # Eğer bir satırın modeli, bir grubun içindeyse, adını Grup Adı yap.
        if 'Model' in self.df.columns:
            for group_name, members in self.groups.items():
                # Gizli grupları uygulama (Onları filtreleyeceğiz)
                mask = self.df['Model'].isin(members)
                self.df.loc[mask, 'Model'] = group_name

        # 2. Gizleme Mantığı
        # Eğer bir "Model" (veya grup adı), hidden_groups içindeyse, o satırları veriden at.
        if 'Model' in self.df.columns:
            self.df = self.df[~self.df['Model'].isin(self.hidden_groups)]

    def get_column_data(self, col_name):
        if self.df is not None and col_name in self.df.columns:
            return self.df[col_name].dropna().unique().tolist()
        return []

data_manager = DataManager()

# --- Arayüz Sayfaları ---

class BasePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="#f0f0f0")

class Dashboard(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Üst Bar (Logo ve Başlık)
        header_frame = tk.Frame(self, bg="#333", height=80)
        header_frame.pack(fill="x", side="top")
        
        try:
            logo_path = get_resource_path("logo.webp")
            # Pillow kütüphanesi olmadığı için standart png/gif kullanacağız veya logosuz devam.
            # Kodun çalışması için resim yükleme kısmını try-catch ile geçiyorum.
            # Tkinter webp desteklemez, png kullanman daha iyi olur.
            pass 
        except:
            pass

        lbl_title = tk.Label(header_frame, text="Satış Yönetim Paneli", bg="#333", fg="white", font=("Arial", 24, "bold"))
        lbl_title.pack(pady=20)

        # İçerik Alanı
        content_frame = tk.Frame(self, bg="#f0f0f0")
        content_frame.pack(expand=True, fill="both", padx=50, pady=50)

        # Butonlar
        btn_grafik = tk.Button(content_frame, text="📊 Grafikler ve Raporlar", font=("Arial", 16),
                               bg="#007bff", fg="white", height=2,
                               command=lambda: controller.show_frame("GraphPage"))
        btn_grafik.pack(fill="x", pady=10)

        btn_simulasyon = tk.Button(content_frame, text="🚀 Satış Simülasyonu", font=("Arial", 16),
                                   bg="#28a745", fg="white", height=2,
                                   command=self.start_simulation)
        btn_simulasyon.pack(fill="x", pady=10)

        btn_ayarlar = tk.Button(content_frame, text="⚙️ Ayarlar", font=("Arial", 16),
                                bg="#6c757d", fg="white", height=2,
                                command=lambda: controller.show_frame("SettingsPage"))
        btn_ayarlar.pack(fill="x", pady=10)

        btn_cikis = tk.Button(content_frame, text="Çıkış", font=("Arial", 12),
                              bg="#dc3545", fg="white", command=parent.quit)
        btn_cikis.pack(fill="x", pady=30)

    def start_simulation(self):
        # Simülasyonu sıfırdan başlat
        if data_manager.df is None:
             messagebox.showwarning("Uyarı", "Lütfen önce veri dosyası yükleyin.")
             return
        self.controller.simulation_data = {} # Seçimleri sıfırla
        self.controller.show_frame("SimSelectConsultant")

class GraphPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        # Üst Bar
        nav_frame = tk.Frame(self, bg="#ddd", height=50)
        nav_frame.pack(fill="x", side="top")
        
        btn_back = tk.Button(nav_frame, text="< Geri Dön", command=lambda: controller.show_frame("Dashboard"))
        btn_back.pack(side="left", padx=10, pady=10)

        # Grafik Alanı (Canvas) ve Scrollbar
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Grafik çizdirme fonksiyonunu çağıracağız
        # Not: Dinamik güncelleme için show_frame tetiklendiğinde çizim yenilenmeli.
        self.bind("<<Show>>", self.update_graphs)

    def update_graphs(self, event=None):
        if data_manager.df is None:
            return

        # Temizle
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        # Scrollable Frame yapısı
        canvas = tk.Canvas(self.canvas_frame)
        scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Grafik 1: Satış / Kayıp Oranı ---
        if 'Status' in data_manager.df.columns:
            fig1 = self.create_pie_chart(data_manager.df['Status'].value_counts(), "Genel Satış Durumu")
            self.add_chart_to_frame(fig1, scrollable_frame)

        # --- Grafik 2: Model Bazlı Satışlar (Dinamik Boyutlu) ---
        if 'Model' in data_manager.df.columns:
            model_counts = data_manager.df['Model'].value_counts()
            fig2 = self.create_bar_chart(model_counts, "Model Dağılımı")
            self.add_chart_to_frame(fig2, scrollable_frame)

        # --- Grafik 3: Danışman Performansı ---
        if 'Sales Consultant' in data_manager.df.columns:
            cons_counts = data_manager.df['Sales Consultant'].value_counts()
            fig3 = self.create_bar_chart(cons_counts, "Danışman Görüşme Sayıları")
            self.add_chart_to_frame(fig3, scrollable_frame)

    def create_pie_chart(self, data, title):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(data, labels=data.index, autopct='%1.1f%%', startangle=90)
        ax.set_title(title)
        return fig

    def create_bar_chart(self, data, title):
        # YAZI UZUNLUĞUNA GÖRE BOYUT AYARLAMA (İstek 1 ve 4)
        
        # En uzun etiketi bul
        max_label_len = 0
        if len(data.index) > 0:
            max_label_len = max([len(str(i)) for i in data.index])
        
        # Grafik yüksekliği ve alt boşluğu hesapla
        # Her 10 karakter için yaklaşık 0.1 bottom margin ekle, minimum 0.2 olsun.
        bottom_margin = 0.2 + (max_label_len * 0.015)
        if bottom_margin > 0.6: bottom_margin = 0.6 # Çok da abartma

        # Grafik genişliği: Veri sayısı arttıkça genişlesin
        width = max(8, len(data) * 0.5) 

        fig, ax = plt.subplots(figsize=(width, 6)) # Genişlik dinamik, yükseklik sabit
        data.plot(kind='bar', ax=ax, color='#17a2b8')
        
        ax.set_title(title)
        
        # Etiketleri 45 derece çevir ve sağa hizala (Okunabilirlik için en iyi yöntem)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Alttan boşluk bırak (Uzun yazılar kesilmesin)
        plt.subplots_adjust(bottom=bottom_margin)
        
        return fig

    def add_chart_to_frame(self, fig, frame):
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20, padx=10)

# --- Simülasyon Sayfaları (Adım Adım) ---

class SimSelectConsultant(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tk.Label(self, text="Adım 1: Danışman Seçin", font=("Arial", 20, "bold"), bg="#f0f0f0").pack(pady=30)
        
        self.frame_buttons = tk.Frame(self, bg="#f0f0f0")
        self.frame_buttons.pack(expand=True, fill="both", padx=50)

        self.bind("<<Show>>", self.populate_consultants)

    def populate_consultants(self, event=None):
        for widget in self.frame_buttons.winfo_children():
            widget.destroy()

        if data_manager.df is None or 'Sales Consultant' not in data_manager.df.columns:
            tk.Label(self.frame_buttons, text="Veri bulunamadı.", bg="#f0f0f0").pack()
            return

        consultants = sorted(data_manager.df['Sales Consultant'].dropna().unique())
        
        for cons in consultants:
            btn = tk.Button(self.frame_buttons, text=cons, font=("Arial", 12), height=2,
                            command=lambda c=cons: self.next_step(c))
            btn.pack(fill="x", pady=5)
        
        tk.Button(self, text="İptal", command=lambda: self.controller.show_frame("Dashboard"), bg="#dc3545", fg="white").pack(pady=20)

    def next_step(self, selection):
        self.controller.simulation_data['consultant'] = selection
        self.controller.show_frame("SimSelectModel")

class SimSelectModel(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tk.Label(self, text="Adım 2: İlgilenilen Modeli Seçin", font=("Arial", 20, "bold"), bg="#f0f0f0").pack(pady=30)
        
        self.frame_buttons = tk.Frame(self, bg="#f0f0f0")
        self.frame_buttons.pack(expand=True, fill="both", padx=50)

        self.bind("<<Show>>", self.populate_models)

    def populate_models(self, event=None):
        for widget in self.frame_buttons.winfo_children():
            widget.destroy()

        # Gruplanmış ve Gizlenmiş verileri zaten DataManager halletti.
        # Sadece mevcut 'Model' sütunundaki unique değerleri alacağız.
        models = sorted(data_manager.df['Model'].dropna().unique())
        
        for model in models:
            btn = tk.Button(self.frame_buttons, text=model, font=("Arial", 12), height=2,
                            command=lambda m=model: self.next_step(m))
            btn.pack(fill="x", pady=5)

        tk.Button(self, text="< Geri", command=lambda: self.controller.show_frame("SimSelectConsultant")).pack(side="left", padx=20, pady=20)

    def next_step(self, selection):
        self.controller.simulation_data['model'] = selection
        self.controller.show_frame("SimSelectMonth")

class SimSelectMonth(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tk.Label(self, text="Adım 3: Dönem (Ay) Seçin", font=("Arial", 20, "bold"), bg="#f0f0f0").pack(pady=30)
        
        self.frame_buttons = tk.Frame(self, bg="#f0f0f0")
        self.frame_buttons.pack(expand=True, fill="both", padx=50)
        
        # Aylar genelde sabittir ama veriden de çekebiliriz.
        # Veride 'Date' veya 'Month' sütunu var mı kontrol etmeliyiz.
        # Yoksa manuel liste. Biz manuel liste yapalım şimdilik, veride tarih sütunu formatı karışık olabilir.
        self.months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                       "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

        for month in self.months:
            btn = tk.Button(self.frame_buttons, text=month, font=("Arial", 10),
                            command=lambda m=month: self.next_step(m))
            btn.pack(fill="x", pady=2)

        tk.Button(self, text="< Geri", command=lambda: self.controller.show_frame("SimSelectModel")).pack(side="left", padx=20, pady=20)

    def next_step(self, selection):
        self.controller.simulation_data['month'] = selection
        self.controller.show_frame("SimResult")

class SimResult(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        # Değişkenler
        self.w_cons = tk.DoubleVar(value=50.0)
        self.w_model = tk.DoubleVar(value=30.0)
        self.w_month = tk.DoubleVar(value=20.0)
        
        self.selected_model_var = tk.StringVar()
        self.selected_month_var = tk.StringVar()

        # Üst Başlık
        tk.Label(self, text="Simülasyon Sonucu & Analiz", font=("Arial", 22, "bold"), bg="#f0f0f0").pack(pady=10)

        # 1. Bölüm: Sonuç Göstergesi (Büyük Puan)
        self.lbl_result = tk.Label(self, text="% --", font=("Arial", 40, "bold"), fg="#28a745", bg="#f0f0f0")
        self.lbl_result.pack(pady=10)
        self.lbl_detail = tk.Label(self, text="Hesaplanıyor...", font=("Arial", 12), bg="#f0f0f0")
        self.lbl_detail.pack()

        # 2. Bölüm: Senaryo Değiştirme (Excel Tarzı Kutular)
        frame_scenario = tk.LabelFrame(self, text="Senaryoyu Düzenle (What-If)", bg="#f0f0f0", padx=10, pady=10)
        frame_scenario.pack(fill="x", padx=20, pady=10)
        
        tk.Label(frame_scenario, text="Model:", bg="#f0f0f0").grid(row=0, column=0, padx=5)
        self.combo_model = ttk.Combobox(frame_scenario, textvariable=self.selected_model_var, state="readonly")
        self.combo_model.grid(row=0, column=1, padx=5)
        self.combo_model.bind("<<ComboboxSelected>>", self.recalculate)

        tk.Label(frame_scenario, text="Ay:", bg="#f0f0f0").grid(row=0, column=2, padx=5)
        self.combo_month = ttk.Combobox(frame_scenario, textvariable=self.selected_month_var, values=["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], state="readonly")
        self.combo_month.grid(row=0, column=3, padx=5)
        self.combo_month.bind("<<ComboboxSelected>>", self.recalculate)

        # 3. Bölüm: Ağırlık Ayarları (Slider)
        frame_weights = tk.LabelFrame(self, text="Etki Ağırlıkları (%)", bg="#f0f0f0", padx=10, pady=10)
        frame_weights.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_weights, text="Danışman:", bg="#f0f0f0").grid(row=0, column=0)
        s1 = tk.Scale(frame_weights, variable=self.w_cons, from_=0, to=100, orient="horizontal", command=self.recalculate)
        s1.grid(row=0, column=1, sticky="ew")

        tk.Label(frame_weights, text="Model:", bg="#f0f0f0").grid(row=1, column=0)
        s2 = tk.Scale(frame_weights, variable=self.w_model, from_=0, to=100, orient="horizontal", command=self.recalculate)
        s2.grid(row=1, column=1, sticky="ew")

        tk.Label(frame_weights, text="Dönem:", bg="#f0f0f0").grid(row=2, column=0)
        s3 = tk.Scale(frame_weights, variable=self.w_month, from_=0, to=100, orient="horizontal", command=self.recalculate)
        s3.grid(row=2, column=1, sticky="ew")
        
        # 4. Bölüm: Yapay Zeka Önerisi
        self.lbl_suggestion = tk.Label(self, text="", font=("Arial", 11, "italic"), fg="blue", bg="#f0f0f0", wraplength=400)
        self.lbl_suggestion.pack(pady=10)

        # Alt Butonlar
        tk.Button(self, text="Ana Menü", command=lambda: self.controller.show_frame("Dashboard")).pack(pady=10)

        self.bind("<<Show>>", self.initialize_view)

    def initialize_view(self, event=None):
        # Combobox içeriklerini doldur
        if data_manager.df is not None:
             self.combo_model['values'] = sorted(data_manager.df['Model'].dropna().unique())
        
        # Seçimleri yerleştir
        data = self.controller.simulation_data
        self.selected_model_var.set(data.get('model', ''))
        self.selected_month_var.set(data.get('month', ''))
        
        self.recalculate()

    def calculate_conversion_rate(self, filter_col, filter_val):
        """Basit dönüşüm oranı hesaplayıcı: (Satış / Toplam) * 100"""
        if data_manager.df is None: return 0
        
        # Filtrele
        subset = data_manager.df[data_manager.df[filter_col] == filter_val]
        if len(subset) == 0: return 0
        
        # Satış sayısını bul (Status sütunu 'Sold' veya 'Satış' içeriyorsa)
        # Burası Excelindeki veriye göre değişir. Varsayalım "Status" sütununda "Satış" yazıyor.
        # Eğer sütun yoksa veya değer yoksa varsayılan bir oran döndürür.
        if 'Status' not in subset.columns: return 15.0 # Dummy
        
        sales = subset[subset['Status'].astype(str).str.contains("Satış", case=False, na=False)]
        rate = (len(sales) / len(subset)) * 100
        return rate

    def recalculate(self, event=None):
        cons = self.controller.simulation_data.get('consultant', '')
        model = self.selected_model_var.get()
        month = self.selected_month_var.get()
        
        # 1. Oranları Hesapla (Veriden)
        rate_cons = self.calculate_conversion_rate('Sales Consultant', cons)
        rate_model = self.calculate_conversion_rate('Model', model)
        rate_month = 10.0 # Ay verisi olmadığı için sabit bir değer veya random. Veri setinde Ay sütunu varsa oradan çekilir.
        
        # Eğer Excelde 'Month' sütunu varsa:
        # rate_month = self.calculate_conversion_rate('Month', month)

        # 2. Ağırlıklı Ortalama
        w_c = self.w_cons.get()
        w_m = self.w_model.get()
        w_mo = self.w_month.get()
        
        total_w = w_c + w_m + w_mo
        if total_w == 0: total_w = 1
        
        final_score = (rate_cons * w_c + rate_model * w_m + rate_month * w_mo) / total_w
        
        # Ekrana Bas
        self.lbl_result.config(text=f"%{final_score:.1f}")
        self.lbl_detail.config(text=f"Danışman: %{rate_cons:.1f} | Model: %{rate_model:.1f} | Dönem: %{rate_month:.1f}")

        # 3. Öneriler (Basit Mantık)
        suggestions = []
        if rate_model < 10:
            suggestions.append(f"⚠️ {model} modelinin dönüşüm oranı düşük. Başka bir modele yönlendirme yapmayı düşünün.")
        if w_c < 20:
            suggestions.append("ℹ️ Danışman etkisini çok düşük ayarladınız. Satışta insan faktörü önemlidir.")
        
        if not suggestions:
            self.lbl_suggestion.config(text="✅ Mevcut senaryo dengeli görünüyor.")
        else:
            self.lbl_suggestion.config(text="\n".join(suggestions))


class SettingsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self, text="Ayarlar", font=("Arial", 20), bg="#f0f0f0").pack(pady=20)
        
        # Dosya Seçimi
        frame_file = tk.Frame(self, bg="#f0f0f0")
        frame_file.pack(pady=10)
        
        self.lbl_file = tk.Label(frame_file, text="Dosya: Seçilmedi", bg="#f0f0f0")
        self.lbl_file.pack(side="left", padx=10)
        
        btn_select = tk.Button(frame_file, text="Dosya Seç / Değiştir", command=self.select_file)
        btn_select.pack(side="left")

        # Gruplama ve Gizleme Bölümü
        self.tree_frame = tk.Frame(self, bg="#f0f0f0")
        self.tree_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Treeview (Tablo)
        cols = ("Ham Veri", "Grup Adı", "Durum")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show='headings')
        self.tree.heading("Ham Veri", text="Ham Veri (Model)")
        self.tree.heading("Grup Adı", text="Atanan Grup")
        self.tree.heading("Durum", text="Görünürlük")
        self.tree.pack(side="left", fill="both", expand=True)

        # Scrollbar
        sb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # Kontrol Butonları
        btn_frame = tk.Frame(self, bg="#f0f0f0")
        btn_frame.pack(fill="x", padx=20)
        
        tk.Button(btn_frame, text="Seçiliyi Grupla", command=self.create_group).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Seçiliyi Gizle/Göster", command=self.toggle_hide).pack(side="left", padx=5) # YENİ ÖZELLİK
        tk.Button(btn_frame, text="Grubu Sil", command=self.delete_group_assignment).pack(side="left", padx=5)

        # Alt Butonlar
        bottom_frame = tk.Frame(self, bg="#f0f0f0")
        bottom_frame.pack(pady=20)
        
        tk.Button(bottom_frame, text="Kaydet ve Çık", bg="#28a745", fg="white", 
                  command=lambda: [data_manager.save_config(), controller.show_frame("Dashboard")]).pack(side="left", padx=10)
        
        tk.Button(bottom_frame, text="Kaydetmeden Çık", bg="#dc3545", fg="white", 
                  command=lambda: [data_manager.load_config(), controller.show_frame("Dashboard")]).pack(side="left", padx=10) # İSTEK 3

        self.bind("<<Show>>", self.refresh_tree)

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv")])
        if filename:
            if data_manager.load_data(filename):
                self.lbl_file.config(text=f"Dosya: {os.path.basename(filename)}")
                self.refresh_tree()

    def refresh_tree(self, event=None):
        # Tabloyu temizle
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if data_manager.raw_df is None: return
        self.lbl_file.config(text=f"Dosya: {os.path.basename(data_manager.file_path)}")

        # Modelleri listele
        if 'Model' in data_manager.raw_df.columns:
            unique_models = sorted(data_manager.raw_df['Model'].dropna().unique())
            
            for model in unique_models:
                # Grubunu bul
                assigned_group = "-"
                for g_name, members in data_manager.groups.items():
                    if model in members:
                        assigned_group = g_name
                        break
                
                # Gizlilik Durumu
                status = "Gizli ❌" if model in data_manager.hidden_groups else "Aktif ✅"
                
                self.tree.insert("", "end", values=(model, assigned_group, status))

    def create_group(self):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        group_name = tk.simpledialog.askstring("Grup", "Grup Adı Girin:")
        if not group_name: return

        if group_name not in data_manager.groups:
            data_manager.groups[group_name] = []

        for item in selected_items:
            model_name = self.tree.item(item)['values'][0]
            # Eski gruptan çıkar (varsa)
            for g in data_manager.groups.values():
                if model_name in g: g.remove(model_name)
            
            # Yeni gruba ekle
            data_manager.groups[group_name].append(model_name)
        
        data_manager.process_data() # Veriyi güncelle
        self.refresh_tree()

    def toggle_hide(self):
        # Seçili öğeleri gizle veya göster
        selected_items = self.tree.selection()
        if not selected_items: return
        
        for item in selected_items:
            model_name = self.tree.item(item)['values'][0]
            
            if model_name in data_manager.hidden_groups:
                data_manager.hidden_groups.remove(model_name)
            else:
                data_manager.hidden_groups.append(model_name)
        
        data_manager.process_data()
        self.refresh_tree()

    def delete_group_assignment(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            model_name = self.tree.item(item)['values'][0]
            for g in data_manager.groups.values():
                if model_name in g: g.remove(model_name)
        
        data_manager.process_data()
        self.refresh_tree()

# --- Ana Uygulama ---

class SalesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Satış Simülasyonu ve Yönetim Paneli")
        self.geometry("1000x700")
        
        # Simülasyon verilerini tutacak sözlük
        self.simulation_data = {} 

        # Container (Sayfaların tutulduğu yer)
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Tüm sayfaları buraya ekliyoruz
        for F in (Dashboard, GraphPage, SettingsPage, SimSelectConsultant, SimSelectModel, SimSelectMonth, SimResult):
            page_name = F.__name__
            frame = F(container, self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # İlk veri yükleme denemesi
        data_manager.load_config()
        if data_manager.file_path:
            data_manager.load_data()

        self.show_frame("Dashboard")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        frame.event_generate("<<Show>>") # Sayfa açıldığında tetikle

if __name__ == "__main__":
    app = SalesApp()
    app.mainloop()
