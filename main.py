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
        self.root.geometry("1200x850")
        self.root.configure(bg="#2c3e50")

        self.df = None
        self.groups = {}
        self.hidden_items = [] # Gizlenen veriler listesi
        self.current_file_path = ""
        
        # Simülasyon Seçimleri
        self.sim_choices = {"consultant": None, "model": None, "month": "Ocak"}
        self.weights = {"consultant": 50, "model": 30, "month": 20}

        self.load_config()
        
        # İlk açılış kontrolü
        if self.current_file_path and os.path.exists(self.current_file_path):
            self.load_data(self.current_file_path, silent=True)
        else:
            self.create_main_menu() # Dosya yoksa direkt menüyü aç, oradan seçsin

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_file_path = data.get("last_file", "")
                    self.groups = data.get("groups", {})
                    self.hidden_items = data.get("hidden_items", [])
            except:
                pass

    def save_config(self):
        data = {
            "last_file": self.current_file_path,
            "groups": self.groups,
            "hidden_items": self.hidden_items
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
            
            # --- İSTEK 2: GRUP TEMİZLİĞİ ---
            # Yeni dosya yüklendiğinde, eğer gruplardaki bir eleman yeni dosyada hiç yoksa gruptan sil.
            # Ancak yeni dosyada varsa (ortaksa) kalsın.
            if 'Model' in self.df.columns:
                existing_models = set(self.df['Model'].dropna().unique())
                
                # Grupları gez ve temizle
                for group_name, members in list(self.groups.items()):
                    # Sadece mevcut veride olanları tut
                    valid_members = [m for m in members if m in existing_models]
                    self.groups[group_name] = valid_members
                    # Eğer grup boşaldıysa grubu da silebiliriz (isteğe bağlı, şimdilik tutuyoruz)

            self.save_config()
            
            if not silent:
                messagebox.showinfo("Başarılı", "Veri dosyası yüklendi ve gruplar optimize edildi.")
                self.create_main_menu()
            else:
                self.create_main_menu()
                
        except Exception as e:
            if not silent:
                messagebox.showerror("Hata", f"Dosya okunamadı:\n{e}")
            self.create_main_menu()

    def get_processed_data(self):
        """Grupları uygular ve GİZLİ verileri filtreler"""
        if self.df is None: return None
        temp_df = self.df.copy()
        
        # Boşluk temizliği
        temp_df.columns = temp_df.columns.str.strip()
        
        if 'Model' in temp_df.columns:
            # 1. Grupları Uygula
            for grp_name, members in self.groups.items():
                mask = temp_df['Model'].isin(members)
                temp_df.loc[mask, 'Model'] = grp_name
            
            # 2. Gizli Verileri Çıkar (İSTEK 3 - Gizleme)
            # Hem model hem grup ismi gizli olabilir
            temp_df = temp_df[~temp_df['Model'].isin(self.hidden_items)]
            
        return temp_df

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- ANA MENÜ ---
    def create_main_menu(self):
        self.clear_screen()
        
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(expand=True, fill="both", padx=50, pady=50)

        title = f"Satış Yönetim Paneli"
        if self.current_file_path:
            title += f"\n📂 {os.path.basename(self.current_file_path)}"
        
        tk.Label(main_frame, text=title, font=("Arial", 24, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=30)

        btn_style = {"font": ("Arial", 14), "height": 2, "width": 35, "bd": 0, "cursor": "hand2"}

        # İSTEK 1: Dosya değiştirme seçeneği
        tk.Button(main_frame, text="📂 Dosya Değiştir", command=self.change_file, bg="#3498db", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="📊 Grafikler ve Raporlar", command=self.open_graphs, bg="#e67e22", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="🚀 Satış Simülasyonu", command=self.start_simulation, bg="#27ae60", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="⚙️ Ayarlar", command=self.open_settings, bg="#7f8c8d", fg="white", **btn_style).pack(pady=10)
        tk.Button(main_frame, text="❌ Çıkış", command=self.root.quit, bg="#c0392b", fg="white", **btn_style).pack(pady=30)

    def change_file(self):
        file_path = filedialog.askopenfilename(title="Yeni Veri Dosyası Seç", filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv")])
        if file_path:
            self.load_data(file_path)

    # --- GRAFİKLER (İSTEK 4: Dinamik Boyutlandırma) ---
    def open_graphs(self):
        self.clear_screen()
        
        nav = tk.Frame(self.root, bg="#34495e", height=50)
        nav.pack(side="top", fill="x")
        tk.Button(nav, text="< Ana Menü", command=self.create_main_menu, bg="#e74c3c", fg="white").pack(side="left", padx=20, pady=10)

        data = self.get_processed_data()
        if data is None:
            tk.Label(self.root, text="Veri Yok!", bg="#2c3e50", fg="white").pack(pady=50)
            return

        # Scrollbar Alanı
        canvas = tk.Canvas(self.root, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#ecf0f1")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Grafik 1
        if 'Model' in data.columns:
            self.create_dynamic_chart(scroll_frame, data['Model'].value_counts(), "Model Dağılımı")

        # Grafik 2
        if 'Sales Consultant' in data.columns:
            self.create_dynamic_chart(scroll_frame, data['Sales Consultant'].value_counts(), "Danışman Performansı")

    def create_dynamic_chart(self, parent, data, title):
        if len(data) == 0: return

        # --- DİNAMİK BOYUT HESAPLAMA ---
        # En uzun etiketi bul
        max_len = max([len(str(x)) for x in data.index])
        
        # Her harf için alt boşluğu artır (Matplotlib margin)
        # 0.15 standart, her harf için 0.015 ekle
        bottom_margin = 0.15 + (max_len * 0.015)
        # Sınır koy (grafik tamamen kaybolmasın)
        if bottom_margin > 0.60: bottom_margin = 0.60

        # Grafik yüksekliğini de veriye göre artır (harfler sığsın diye)
        fig_height = 6 + (max_len * 0.05)

        fig, ax = plt.subplots(figsize=(10, fig_height))
        data.plot(kind='bar', ax=ax, color='#2980b9', edgecolor='black')
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right') # 45 derece eğik
        
        # Dinamik boşluğu uygula
        plt.subplots_adjust(bottom=bottom_margin)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=30, padx=20)

    # --- SİMÜLASYON (İSTEK 5: 4 Adımlı Tam Süreç) ---
    def start_simulation(self):
        self.sim_choices = {"consultant": None, "model": None, "month": None}
        self.sim_step_1()

    # ADIM 1: DANIŞMAN
    def sim_step_1(self):
        self.clear_screen()
        data = self.get_processed_data()
        
        tk.Label(self.root, text="Satış Simülasyonu - Adım 1", font=("Arial", 20, "bold"), bg="#2c3e50", fg="white").pack(pady=20)
        tk.Label(self.root, text="Lütfen bir Danışman seçin:", font=("Arial", 14), bg="#2c3e50", fg="#bdc3c7").pack(pady=10)
        
        frame_grid = tk.Frame(self.root, bg="#2c3e50")
        frame_grid.pack(expand=True, padx=50)

        if data is not None and 'Sales Consultant' in data.columns:
            items = sorted(data['Sales Consultant'].dropna().unique())
            self.create_grid(frame_grid, items, self.sim_step_2)
        
        self.add_sim_cancel_btn()

    # ADIM 2: MODEL
    def sim_step_2(self, selection):
        self.sim_choices['consultant'] = selection
        self.clear_screen()
        data = self.get_processed_data()

        tk.Label(self.root, text="Satış Simülasyonu - Adım 2", font=("Arial", 20, "bold"), bg="#2c3e50", fg="white").pack(pady=20)
        tk.Label(self.root, text="Lütfen bir Model seçin:", font=("Arial", 14), bg="#2c3e50", fg="#bdc3c7").pack(pady=10)

        frame_grid = tk.Frame(self.root, bg="#2c3e50")
        frame_grid.pack(expand=True, padx=50)

        if data is not None and 'Model' in data.columns:
            # Gruplanmış ve gizlenmiş verileri zaten get_processed_data halletti
            items = sorted(data['Model'].dropna().unique())
            self.create_grid(frame_grid, items, self.sim_step_3)

        self.add_sim_cancel_btn()

    # ADIM 3: AY
    def sim_step_3(self, selection):
        self.sim_choices['model'] = selection
        self.clear_screen()

        tk.Label(self.root, text="Satış Simülasyonu - Adım 3", font=("Arial", 20, "bold"), bg="#2c3e50", fg="white").pack(pady=20)
        tk.Label(self.root, text="Lütfen Dönem (Ay) seçin:", font=("Arial", 14), bg="#2c3e50", fg="#bdc3c7").pack(pady=10)

        frame_grid = tk.Frame(self.root, bg="#2c3e50")
        frame_grid.pack(expand=True, padx=50)

        months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        self.create_grid(frame_grid, months, self.sim_step_4_result)

        self.add_sim_cancel_btn()

    # ADIM 4: SONUÇ ve ANALİZ
    def sim_step_4_result(self, selection):
        self.sim_choices['month'] = selection
        self.show_result_screen()

    def show_result_screen(self):
        self.clear_screen()
        main = tk.Frame(self.root, bg="#ecf0f1")
        main.pack(fill="both", expand=True)

        tk.Label(main, text="🎯 Simülasyon Sonucu", font=("Arial", 22, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=10)

        # Skor Paneli
        frame_score = tk.Frame(main, bg="white", bd=2, relief="groove")
        frame_score.pack(fill="x", padx=50, pady=5)
        self.lbl_score = tk.Label(frame_score, text="--", font=("Arial", 36, "bold"), fg="#27ae60", bg="white")
        self.lbl_score.pack(pady=5)
        self.lbl_info = tk.Label(frame_score, text="...", bg="white", fg="#7f8c8d")
        self.lbl_info.pack()

        # What-If (Senaryo Değiştirme)
        frame_controls = tk.LabelFrame(main, text="Senaryoyu Değiştir", bg="#ecf0f1", font=("Arial", 11, "bold"))
        frame_controls.pack(fill="x", padx=50, pady=10)
        
        # Comboboxlar
        data = self.get_processed_data()
        all_cons = sorted(data['Sales Consultant'].dropna().unique()) if data is not None else []
        all_mods = sorted(data['Model'].dropna().unique()) if data is not None else []
        all_mons = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

        self.cb_cons = ttk.Combobox(frame_controls, values=all_cons, state="readonly"); self.cb_cons.set(self.sim_choices['consultant']); self.cb_cons.grid(row=0, column=0, padx=5, pady=5)
        self.cb_model = ttk.Combobox(frame_controls, values=all_mods, state="readonly"); self.cb_model.set(self.sim_choices['model']); self.cb_model.grid(row=0, column=1, padx=5, pady=5)
        self.cb_month = ttk.Combobox(frame_controls, values=all_mons, state="readonly"); self.cb_month.set(self.sim_choices['month']); self.cb_month.grid(row=0, column=2, padx=5, pady=5)

        for cb in [self.cb_cons, self.cb_model, self.cb_month]: cb.bind("<<ComboboxSelected>>", self.recalculate)

        # Ağırlıklar
        frame_weights = tk.LabelFrame(main, text="Ağırlıklar (%)", bg="#ecf0f1")
        frame_weights.pack(fill="x", padx=50, pady=5)
        self.s_cons = tk.Scale(frame_weights, from_=0, to=100, orient="horizontal", label="Danışman", command=lambda x: self.recalculate()); self.s_cons.set(self.weights['consultant']); self.s_cons.pack(side="left", fill="x", expand=True)
        self.s_model = tk.Scale(frame_weights, from_=0, to=100, orient="horizontal", label="Model", command=lambda x: self.recalculate()); self.s_model.set(self.weights['model']); self.s_model.pack(side="left", fill="x", expand=True)
        self.s_month = tk.Scale(frame_weights, from_=0, to=100, orient="horizontal", label="Dönem", command=lambda x: self.recalculate()); self.s_month.set(self.weights['month']); self.s_month.pack(side="left", fill="x", expand=True)

        # Öneriler (Yapay Zeka)
        self.lbl_suggestion = tk.Label(main, text="", font=("Arial", 11, "italic"), fg="#d35400", bg="#ecf0f1")
        self.lbl_suggestion.pack(pady=10)

        tk.Button(main, text="Ana Menü", command=self.create_main_menu, bg="#34495e", fg="white").pack(pady=10)

        self.recalculate()

    def recalculate(self, event=None):
        c = self.cb_cons.get()
        m = self.cb_model.get()
        mo = self.cb_month.get()
        
        # Basit Puanlama Simülasyonu (Veri olmadığı için adede göre puan uyduruyoruz)
        def get_score(col, val):
            if self.df is None or col not in self.df.columns: return 50
            count = len(self.df[self.df[col] == val])
            return min(95, count * 2 + 10) # Formül

        score_c = get_score('Sales Consultant', c)
        score_m = get_score('Model', m)
        score_mo = 50 # Ay verisi olmadığı için sabit
        
        wc, wm, wmo = self.s_cons.get(), self.s_model.get(), self.s_month.get()
        total = wc + wm + wmo if (wc+wm+wmo) > 0 else 1
        
        final = (score_c*wc + score_m*wm + score_mo*wmo) / total
        self.lbl_score.config(text=f"%{final:.1f}")
        self.lbl_info.config(text=f"Danışman: {score_c} | Model: {score_m} | Dönem: {score_mo}")

        # ÖNERİ SİSTEMİ
        suggestions = []
        if score_m < 40: suggestions.append(f"⚠️ '{m}' modelinin geçmiş performansı düşük. Popüler modellere yönelin.")
        if final < 50: suggestions.append(f"💡 Başka bir ay seçimi veya danışman değişikliği oranı artırabilir.")
        
        self.lbl_suggestion.config(text="\n".join(suggestions) if suggestions else "✅ Senaryo olumlu görünüyor.")

    def create_grid(self, frame, items, cmd):
        r, c = 0, 0
        for item in items:
            tk.Button(frame, text=item, width=20, height=2, command=lambda x=item: cmd(x), bg="#3498db", fg="white").grid(row=r, column=c, padx=5, pady=5)
            c += 1
            if c > 3: c=0; r+=1

    def add_sim_cancel_btn(self):
        tk.Button(self.root, text="İptal", command=self.create_main_menu, bg="#c0392b", fg="white").pack(pady=20)

    # --- AYARLAR (İSTEK 3: GİZLEME TUŞU ve KAYDETMEDEN ÇIK) ---
    def open_settings(self):
        self.clear_screen()
        tk.Label(self.root, text="Ayarlar", font=("Arial", 20, "bold"), bg="#2c3e50", fg="white").pack(pady=20)

        frame_list = tk.Frame(self.root); frame_list.pack(fill="both", expand=True, padx=50)
        
        cols = ("Veri", "Grup", "Durum")
        tree = ttk.Treeview(frame_list, columns=cols, show='headings')
        tree.heading("Veri", text="Model Adı"); tree.heading("Grup", text="Grup"); tree.heading("Durum", text="Durum")
        tree.pack(side="left", fill="both", expand=True)
        
        if self.df is not None and 'Model' in self.df.columns:
            # Hem dosyadaki hem gruptaki verileri birleştir
            all_items = set(self.df['Model'].dropna().unique())
            for g in self.groups.values():
                for i in g: all_items.add(i)
            
            for item in sorted(all_items):
                grp = "-"
                for gname, gmems in self.groups.items():
                    if item in gmems: grp = gname; break
                
                # İSTEK 3: Gizli mi değil mi?
                status = "❌ GİZLİ (Hesaplanmaz)" if item in self.hidden_items else "✅ AKTİF"
                tree.insert("", "end", values=(item, grp, status))

        # Kontroller
        frame_btns = tk.Frame(self.root, bg="#2c3e50"); frame_btns.pack(pady=10)
        tk.Button(frame_btns, text="👁️ Seçiliyi Gizle/Göster", command=lambda: self.toggle_hide(tree), bg="#f39c12", fg="white", width=20).pack(side="left", padx=5)
        tk.Button(frame_btns, text="🔗 Grupla", command=lambda: self.create_group(tree), bg="#3498db", fg="white", width=20).pack(side="left", padx=5)

        # Alt Butonlar (İSTEK: Kaydetmeden Çık)
        frame_bot = tk.Frame(self.root, bg="#2c3e50"); frame_bot.pack(pady=20)
        tk.Button(frame_bot, text="💾 Kaydet ve Çık", command=lambda: [self.save_config(), self.create_main_menu()], bg="#27ae60", fg="white", width=20).pack(side="left", padx=10)
        tk.Button(frame_bot, text="🚫 Kaydetmeden Çık", command=lambda: [self.load_config(), self.create_main_menu()], bg="#c0392b", fg="white", width=20).pack(side="left", padx=10)

    def toggle_hide(self, tree):
        sel = tree.selection()
        for s in sel:
            val = tree.item(s)['values'][0]
            if val in self.hidden_items: self.hidden_items.remove(val)
            else: self.hidden_items.append(val)
        self.open_settings()

    def create_group(self, tree):
        sel = tree.selection()
        if not sel: return
        name = simpledialog.askstring("Grup", "Grup Adı:")
        if name:
            if name not in self.groups: self.groups[name] = []
            for s in sel:
                val = tree.item(s)['values'][0]
                # Eskiden çıkar
                for g in self.groups.values():
                    if val in g: g.remove(val)
                self.groups[name].append(val)
            self.open_settings()

if __name__ == "__main__":
    root = tk.Tk()
    app = SatisUygulamasi(root)
    root.mainloop()
