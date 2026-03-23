import pandas as pd
import json
import os
import sys
import base64
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

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


def bayesian_inference(df, genel_oran, prior_strength=5):
    """
    Beta-Binomial Bayesian yaklaşımı.
    Az veri olan kombinasyonlarda genel orana yaklaşır,
    çok veri olduğunda kendi verisine güvenir.
    
    prior_strength: genel oranın ne kadar ağırlıklı olacağı.
    5 = 5 sanal gözlem kadar ağırlık verir genel orana.
    """
    month_names = ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
                   'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık']

    df = df.copy()
    df['Tarih_dt'] = pd.to_datetime(df['Tarih'], errors='coerce')
    df['Ay'] = df['Tarih_dt'].dt.month.apply(
        lambda x: month_names[int(x)-1] if pd.notna(x) else 'Belirtilmemiş'
    )
    df['Hedef'] = (df['Durum'] == 'Satış').astype(int)

    danismanlar = [d for d in df['Danışman Adı'].unique() if d != 'Belirtilmemiş']
    modeller = [m for m in df['Model'].unique() if m != 'Belirtilmemiş']
    aylar = month_names

    # Bayesian prior: genel satış oranı
    alpha_prior = genel_oran * prior_strength
    beta_prior = (1 - genel_oran) * prior_strength

    lookup = {}
    for d in danismanlar:
        for m in modeller:
            for a in aylar:
                subset = df[
                    (df['Danışman Adı'] == d) &
                    (df['Model'] == m) &
                    (df['Ay'] == a)
                ]
                n = len(subset)
                satis = subset['Hedef'].sum()

                # Posterior: prior + gözlemlenen veri
                alpha_post = alpha_prior + satis
                beta_post = beta_prior + (n - satis)
                prob = round((alpha_post / (alpha_post + beta_post)) * 100, 1)

                lookup[f"{d}|{m}|{a}"] = prob

    return lookup


def train_xgboost(df):
    """
    XGBoost modelini eğitir, tüm kombinasyonlar için tahmin üretir
    ve feature importance döndürür.
    """
    month_names = ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
                   'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık']

    df = df.copy()
    df['Tarih_dt'] = pd.to_datetime(df['Tarih'], errors='coerce')
    df['Ay'] = df['Tarih_dt'].dt.month.apply(
        lambda x: month_names[int(x)-1] if pd.notna(x) else 'Belirtilmemiş'
    )
    df['Hedef'] = (df['Durum'] == 'Satış').astype(int)

    features = ['Danışman Adı', 'Model', 'Ay']
    ml_df = df[features + ['Hedef']].copy()
    ml_df = ml_df[ml_df['Danışman Adı'] != 'Belirtilmemiş']
    ml_df = ml_df[ml_df['Model'] != 'Belirtilmemiş']

    if len(ml_df) < 10:
        return None, None

    encoders = {}
    for col in features:
        le = LabelEncoder()
        ml_df[col] = le.fit_transform(ml_df[col].astype(str))
        encoders[col] = le

    X = ml_df[features].values
    y = ml_df['Hedef'].values

    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss',
        verbosity=0
    )
    xgb.fit(X, y)

    # Feature importance (yüzde olarak)
    imp = xgb.feature_importances_
    total = imp.sum()
    feature_importance = {
        'Danışman Adı': round(float(imp[0] / total) * 100, 1),
        'Model':        round(float(imp[1] / total) * 100, 1),
        'Ay':           round(float(imp[2] / total) * 100, 1),
    }

    # Tüm kombinasyonlar için tahmin
    danismanlar = list(encoders['Danışman Adı'].classes_)
    modeller = list(encoders['Model'].classes_)
    aylar = list(encoders['Ay'].classes_)

    lookup = {}
    for d in danismanlar:
        for m in modeller:
            for a in aylar:
                try:
                    d_enc = encoders['Danışman Adı'].transform([d])[0]
                    m_enc = encoders['Model'].transform([m])[0]
                    a_enc = encoders['Ay'].transform([a])[0]
                    X_pred = np.array([[d_enc, m_enc, a_enc]])
                    prob = round(float(xgb.predict_proba(X_pred)[0][1]) * 100, 1)
                    lookup[f"{d}|{m}|{a}"] = prob
                except:
                    continue

    return lookup, feature_importance


def train_models(df):
    try:
        # Genel satış oranı (Bayesian prior için)
        genel_oran = (df['Durum'] == 'Satış').mean()
        if genel_oran == 0:
            genel_oran = 0.1

        xgb_lookup, feature_importance = train_xgboost(df)
        bayes_lookup = bayesian_inference(df, genel_oran)

        if xgb_lookup is None:
            return None

        # İki lookup'ı birleştir
        combined = {}
        for key in bayes_lookup:
            xgb_val = xgb_lookup.get(key, genel_oran * 100)
            bayes_val = bayes_lookup[key]
            avg = round((xgb_val + bayes_val) / 2, 1)
            combined[key] = {
                "xgb": xgb_val,
                "bayes": bayes_val,
                "avg": avg
            }

        return combined, feature_importance

    except Exception as e:
        print(f"Model eğitim hatası: {e}")
        return None, None


def main():
    target_file = get_excel_file()
    if not target_file:
        return

    try:
        df_raw = pd.read_excel(target_file)

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

        raw_models = sorted(df['Model'].dropna().unique().tolist())
        raw_models = [m for m in raw_models if m != 'Belirtilmemiş']

        ml_lookup, feature_importance = train_models(df)
        ml_lookup_json = json.dumps(ml_lookup, ensure_ascii=False) if ml_lookup else 'null'
        fi_json = json.dumps(feature_importance, ensure_ascii=False) if feature_importance else 'null'

        json_data = df.to_json(orient='records', force_ascii=False)

        template_path = resource_path("tasarim.html")
        if not os.path.exists(template_path):
            template_path = "tasarim.html"

        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        html = html.replace("[[JSON_DATA]]", json_data)
        html = html.replace("[[RAW_MODELS]]", json.dumps(raw_models, ensure_ascii=False))
        html = html.replace("[[ML_LOOKUP]]", ml_lookup_json)
        html = html.replace("[[FEATURE_IMPORTANCE]]", fi_json)
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
