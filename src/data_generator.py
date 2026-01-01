import pandas as pd
import numpy as np
from sklearn.datasets import make_blobs
import os

# --- AYARLAR ---
# İstanbul Anadolu Yakası (Kabaca Kadıköy - Ataşehir - Ümraniye üçgeni)
CENTER_LAT = 40.9900
CENTER_LON = 29.0800
STD_DEV = 0.03 # Dağılım genişliği (Yaklaşık 3-4 km yarıçaplı kümeler)

def generate_demand_data(n_samples=200, n_clusters=5, random_state=42):
    """
    Müşteri talep noktaları üretir.
    n_samples: Kaç adet talep noktası (bina/site) olsun?
    n_clusters: Bu noktalar kaç farklı mahallede/öbekte toplansın?
    """
    print("📍 Müşteri talep noktaları üretiliyor...")
    
    # 1. Kümeleme ile koordinat üretimi (Gerçekçi nüfus dağılımı için)
    coords, cluster_labels = make_blobs(
        n_samples=n_samples, 
        centers=n_clusters, 
        cluster_std=STD_DEV * 0.4, 
        center_box=(-STD_DEV, STD_DEV),
        random_state=random_state
    )
    
    # Koordinatları İstanbul merkezine taşı
    lats = coords[:, 0] + CENTER_LAT
    lons = coords[:, 1] + CENTER_LON
    
    # 2. İşletme Verileri Ekleme (BusDev Kısmı)
    # Her noktanın bir talep ağırlığı (günlük sipariş) ve sepet tutarı olsun.
    # Normal dağılım kullanarak rastgelelik ekliyoruz.
    
    df = pd.DataFrame({
        'id': range(1, n_samples + 1),
        'lat': lats,
        'lon': lons,
        'cluster_id': cluster_labels, # Hangi mahallede olduğu
        'daily_orders': np.random.randint(5, 50, size=n_samples), # Günlük 5-50 sipariş arası
        'avg_basket_size': np.random.normal(150, 30, size=n_samples).round(2) # Ort. 150 TL sepet
    })
    
    # Eksi değerleri temizle (Sepet tutarı negatif olamaz)
    df['avg_basket_size'] = df['avg_basket_size'].apply(lambda x: max(x, 50))
    
    print(f"✅ {n_samples} adet talep noktası üretildi.")
    return df

def generate_candidate_sites(n_candidates=20, demand_df=None, random_state=101):
    """
    Potansiyel depo yerleri üretir.
    Mantık: Müşterilerin yoğun olduğu yerlerin aralarına ve biraz dışına rastgele noktalar atar.
    """
    print("🏭 Aday depo lokasyonları belirleniyor...")
    
    if demand_df is None:
        raise ValueError("Önce talep verisi üretilmelidir.")
    
    min_lat, max_lat = demand_df['lat'].min(), demand_df['lat'].max()
    min_lon, max_lon = demand_df['lon'].min(), demand_df['lon'].max()
    
    np.random.seed(random_state)
    
    # Rastgele koordinatlar
    lats = np.random.uniform(min_lat, max_lat, n_candidates)
    lons = np.random.uniform(min_lon, max_lon, n_candidates)
    
    # Depo Özellikleri (IE & Finans Kısmı)
    # Kira: Merkeze yaklaştıkça artmalı (Basit bir simülasyon)
    dist_to_center = np.sqrt((lats - CENTER_LAT)**2 + (lons - CENTER_LON)**2)
    base_rent = 20000 # Baz kira
    rent_costs = base_rent + (1 / (dist_to_center + 0.01)) * 500 # Merkeze yakınsa kira artar
    
    # Kapasite: Büyük depoların kirası daha yüksek olur varsayımı
    capacities = np.random.choice([1000, 1500, 2000, 3000], size=n_candidates)
    
    # Kirayı kapasiteye göre de düzelt
    rent_costs = rent_costs + (capacities * 5) 
    
    df = pd.DataFrame({
        'site_id': [f"D-{i+100}" for i in range(n_candidates)],
        'lat': lats,
        'lon': lons,
        'rent_cost': rent_costs.round(-2), # Son iki haneyi yuvarla
        'capacity': capacities,
        'setup_cost': np.random.choice([150000, 200000], size=n_candidates) # Kurulum maliyeti
    })
    
    print(f"✅ {n_candidates} adet aday depo yeri üretildi.")
    return df

if __name__ == "__main__":
    # --- PROJE KLASÖRÜNÜ BUL ---
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'data', 'raw')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 1. Talep Verisi Üret
    df_demand = generate_demand_data(n_samples=300, n_clusters=6)
    df_demand.to_csv(os.path.join(output_dir, 'demand_points.csv'), index=False)
    
    # 2. Aday Depo Verisi Üret
    df_sites = generate_candidate_sites(n_candidates=30, demand_df=df_demand)
    df_sites.to_csv(os.path.join(output_dir, 'candidate_sites.csv'), index=False)
    
    print("\n🎉 Veri üretim süreci tamamlandı! 'data/raw' klasörünü kontrol et.")