import folium
import pandas as pd
import os

def create_base_map():
    # Dosya yolları
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    demand_path = os.path.join(base_dir, 'data', 'raw', 'demand_points.csv')
    sites_path = os.path.join(base_dir, 'data', 'raw', 'candidate_sites.csv')
    
    # Verileri oku
    df_demand = pd.read_csv(demand_path)
    df_sites = pd.read_csv(sites_path)
    
    # Harita Merkezi (Verilerin ortalaması)
    center_lat = df_demand['lat'].mean()
    center_lon = df_demand['lon'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")
    
    # 1. Talep Noktalarını Ekle (Küçük Mavi Noktalar)
    for _, row in df_demand.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=3,
            color='#3498db',
            fill=True,
            fill_opacity=0.6,
            popup=f"Sipariş: {row['daily_orders']} Adet"
        ).add_to(m)
        
    # 2. Aday Depo Noktalarını Ekle (Büyük Kırmızı Markerlar)
    for _, row in df_sites.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            icon=folium.Icon(color='red', icon='warehouse', prefix='fa'),
            tooltip=f"Aday: {row['site_id']} | Kira: {row['rent_cost']} TL"
        ).add_to(m)
        
    # Kaydet
    output_path = os.path.join(base_dir, 'data', 'raw', 'initial_map.html')
    m.save(output_path)
    print(f"🗺️ Harita oluşturuldu: {output_path}")

if __name__ == "__main__":
    create_base_map()