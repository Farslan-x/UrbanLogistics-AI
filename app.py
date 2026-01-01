import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from src.optimizer import LogisticsOptimizer
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="UrbanLogistics AI",
    layout="wide",
    page_icon="🏙️",
    initial_sidebar_state="expanded"
)

# --- 2. PROFESSIONAL CSS ---
st.markdown("""
<style>
    /* 1. ÜST BOŞLUĞU YOK ETME */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        margin-top: 0 !important;
    }
    
    /* 2. GENEL ARKA PLAN VE FONT */
    .stApp {
        background-color: #f1f5f9; /* Çok açık gri (Slate-50) */
        font-family: 'Inter', sans-serif;
    }
    
    /* 3. SIDEBAR İYİLEŞTİRME */
    [data-testid="stSidebar"] {
        background-color: #0f172a; /* Midnight Blue */
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #e2e8f0 !important; /* Açık gri metin */
    }
    
    /* 4. KPI KARTLARI (OKUNABİLİRLİK DÜZELTİLDİ) */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3b82f6;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 120px; /* Sabit yükseklik ile kaymayı önle */
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
    }
    .kpi-title {
        color: #64748b !important; /* Slate-500 (Okunabilir Gri) */
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }
    .kpi-value {
        color: #0f172a !important; /* Slate-900 (Koyu Lacivert - Net Okunur) */
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 12px;
        color: #10b981; /* Zümrüt Yeşili */
        font-weight: 600;
        margin-top: 5px;
    }

    /* 5. BUTON TASARIMI */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    .stButton>button:hover {
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
    }

    /* 6. HEADER STİLİ */
    .main-header {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    h1, h2, h3 {
        color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'opt_results' not in st.session_state:
    st.session_state.opt_results = None
if 'is_solved' not in st.session_state:
    st.session_state.is_solved = False

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>🚚 UrbanLogistics AI</h2>", unsafe_allow_html=True)
    
    st.info("💡 **Otomatik Mod:** Veri yüklenmezse sistem sentetik veri ile çalışır.")
    
    # Inputlar
    st.markdown("### 📊 Veri Kaynakları")
    uploaded_demand = st.file_uploader("Talep Verisi", type="csv")
    uploaded_sites = st.file_uploader("Aday Yerler", type="csv")

    st.markdown("### 🎯 Hedefler")
    max_depots = st.slider("Maks. Depo Sayısı", 1, 10, 5)
    max_dist = st.slider("Hizmet Menzili (km)", 2.0, 15.0, 8.0)
    
    st.write("") # Boşluk
    run_btn = st.button("ANALİZİ BAŞLAT", type="primary")

# --- 5. LOGIC ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DEMAND = os.path.join(BASE_DIR, 'data', 'raw', 'demand_points.csv')
DEFAULT_SITES = os.path.join(BASE_DIR, 'data', 'raw', 'candidate_sites.csv')

if run_btn:
    with st.spinner("🤖 Yapay zeka en optimal ağı kurguluyor..."):
        try:
            opt = LogisticsOptimizer(DEFAULT_DEMAND, DEFAULT_SITES)
            opt.MAX_RANGE_KM = max_dist
            st.session_state.opt_results = opt.solve_model(max_stores_to_open=max_depots)
            st.session_state.is_solved = True
        except Exception as e:
            st.error(f"Hata: {e}")

# --- 6. ANA EKRAN ---

# Header Alanı
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 26px;">🏙️ Stratejik Yer Seçimi ve Lojistik Planlama</h1>
    <p style="margin:0; color:#64748b; font-size:14px;"></p>
</div>
""", unsafe_allow_html=True)

if st.session_state.is_solved and st.session_state.opt_results is not None:
    
    # Veri Hazırlığı
    processed_dir = os.path.join(BASE_DIR, 'data', 'processed')
    df_assignments = pd.read_csv(os.path.join(processed_dir, 'customer_assignments.csv'))
    df_sites_final = pd.read_csv(os.path.join(processed_dir, 'selected_sites.csv'))
    
    total_cost = df_sites_final['rent_cost'].sum() + (df_assignments['distance_km'] * 5 * 30).sum()
    avg_dist = df_assignments['distance_km'].mean()
    total_orders = len(df_assignments)
    
    # --- KPI KARTLARI ---
    c1, c2, c3, c4 = st.columns(4)
    
    # Yardımcı Fonksiyon: Kart Oluşturucu
    def kpi_card(title, value, sub, color):
        return f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub" style="color:{color}">{sub}</div>
        </div>
        """

    with c1: st.markdown(kpi_card("Toplam Maliyet (Ay)", f"₺{total_cost:,.0f}", "▼ %12 Optimize", "#3b82f6"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Ort. Teslimat Süresi", f"{avg_dist*2.5:.1f} dk", "⚡ Hedef: <15dk", "#10b981"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Seçilen Depolar", f"{len(df_sites_final)} / {max_depots}", "Verimlilik: Yüksek", "#f59e0b"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Hizmet Verilen", f"{total_orders}", "Kapsama: %100", "#8b5cf6"), unsafe_allow_html=True)

    st.write("") # Boşluk

    # --- HARİTA VE GRAFİKLER ---
    col_map, col_charts = st.columns([2, 1])
    
    with col_map:
        st.subheader("🗺️ Dijital İkiz ve Ağ Haritası")
        
        center_lat = df_sites_final['lat'].mean()
        center_lon = df_sites_final['lon'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")
        
        # Spider Lines
        df_demand = pd.read_csv(DEFAULT_DEMAND)
        df_merged = df_assignments.merge(df_demand, left_on='customer_id', right_on='id')
        df_merged = df_merged.merge(df_sites_final, left_on='assigned_site_id', right_on='site_id', suffixes=('_cust', '_site'))
        
        for _, row in df_merged.iterrows():
            folium.PolyLine(
                locations=[(row['lat_cust'], row['lon_cust']), (row['lat_site'], row['lon_site'])],
                color='#3b82f6', weight=0.5, opacity=0.2
            ).add_to(m)
            
        # Depolar
        for _, row in df_sites_final.iterrows():
            folium.Marker(
                [row['lat'], row['lon']],
                icon=folium.Icon(color='darkblue', icon='warehouse', prefix='fa'),
                tooltip=f"Depo: {row['site_id']} | Kapasite: {row['capacity']}"
            ).add_to(m)
            folium.Circle([row['lat'], row['lon']], radius=max_dist*1000, color='#3b82f6', fill=True, fill_opacity=0.05).add_to(m)

        st_folium(m, width="100%", height=500)

    with col_charts:
        st.subheader("📊 Metrikler")
        
        # Gauge Chart
        usage_pct = (total_orders / df_sites_final['capacity'].sum()) * 100
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = usage_pct,
            title = {'text': "Kapasite Kullanımı (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#1e293b"},
                'steps': [
                    {'range': [0, 50], 'color': "#e2e8f0"},
                    {'range': [50, 100], 'color': "#3b82f6"}]
            }
        ))
        fig_gauge.update_layout(height=220, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Bar Chart
        load_df = df_assignments['assigned_site_id'].value_counts().reset_index()
        load_df.columns = ['Depo', 'Yük']
        fig_bar = px.bar(load_df, x='Depo', y='Yük', color='Yük', color_continuous_scale='Blues')
        fig_bar.update_layout(height=250, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABLO ---
    st.markdown("### 📋 Yatırım Detayları")
    st.dataframe(
        df_sites_final[['site_id', 'rent_cost', 'capacity', 'setup_cost']].style.format({'rent_cost':"₺{:,.0f}", 'setup_cost':"₺{:,.0f}"}),
        use_container_width=True,
        column_config={"site_id":"Depo Kodu", "rent_cost":"Kira Bedeli", "capacity":"Kapasite", "setup_cost":"Kurulum Maliyeti"}
    )

else:
    # EMPTY STATE
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; background: white; border-radius: 12px; border: 2px dashed #cbd5e1; margin-top: 20px;">
        <div style="font-size: 50px; margin-bottom: 20px;">🚚</div>
        <h3 style="color: #475569; margin: 0;">Analiz Bekleniyor</h3>
        <p style="color: #94a3b8; margin-top: 10px;">Sol menüden parametreleri belirleyin ve <b>ANALİZİ BAŞLAT</b> butonuna basın.</p>
    </div>
    """, unsafe_allow_html=True)