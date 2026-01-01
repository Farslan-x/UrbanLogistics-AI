import pandas as pd
import numpy as np
import pulp
import os
import math

class LogisticsOptimizer:
    def __init__(self, demand_path, sites_path):
        """
        Verileri yükler ve optimizasyon modelini başlatır.
        """
        self.df_demand_path = demand_path # Path'i kaydet (Hata önleyici)
        self.df_demand = pd.read_csv(demand_path)
        self.df_sites = pd.read_csv(sites_path)
        
        # Parametreler (Business Development Kararları)
        self.MAX_RANGE_KM = 8.0  # Bir depo en fazla 8 km uzağa hizmet verebilsin
        self.COST_PER_KM = 5.0   # Km başı taşıma maliyeti (TL)
        
        print(f"📊 Veri Yüklendi: {len(self.df_demand)} Müşteri, {len(self.df_sites)} Aday Depo")

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        İki koordinat arasındaki kuş uçuşu mesafeyi (km) hesaplar.
        """
        R = 6371  # Dünya yarıçapı (km)
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def solve_model(self, max_stores_to_open=5):
        """
        Matematiksel Modeli (MILP) kurar ve çözer.
        """
        print(f"\n⚙️ Optimizasyon Başlıyor... (Hedef: Max {max_stores_to_open} Depo)")
        
        # Kısaltmalar
        I = self.df_demand.index.tolist() # Müşteriler
        J = self.df_sites.index.tolist()  # Aday Depolar
        
        # 1. Mesafe Matrisini Hesapla
        dist_matrix = {}
        valid_pairs = [] # Mesafe kısıtına uyan çiftler
        
        for i in I:
            for j in J:
                d = self._haversine_distance(
                    self.df_demand.loc[i, 'lat'], self.df_demand.loc[i, 'lon'],
                    self.df_sites.loc[j, 'lat'], self.df_sites.loc[j, 'lon']
                )
                if d <= self.MAX_RANGE_KM:
                    dist_matrix[(i, j)] = d
                    valid_pairs.append((i, j))
        
        # 2. MODEL KURULUMU (PuLP)
        prob = pulp.LpProblem("DarkStore_Location_Optimization", pulp.LpMinimize)
        
        # --- KARAR DEĞİŞKENLERİ ---
        # y[j]: Depo j açılacak mı? (1: Evet, 0: Hayır)
        y = pulp.LpVariable.dicts("Open_Depot", J, cat='Binary')
        
        # x[i][j]: Müşteri i, depo j tarafından mı hizmet alacak? (1: Evet, 0: Hayır)
        x = pulp.LpVariable.dicts("Assign", valid_pairs, cat='Binary')

        # --- AMAÇ FONKSİYONU (Minimize Total Cost) ---
        # Sabit Giderler
        fixed_costs = pulp.lpSum([self.df_sites.loc[j, 'rent_cost'] * y[j] for j in J])
        
        # Taşıma Maliyetleri
        transport_costs = pulp.lpSum([
            dist_matrix[(i,j)] * self.COST_PER_KM * self.df_demand.loc[i, 'daily_orders'] * x[(i,j)]
            for (i,j) in valid_pairs
        ])
        
        prob += fixed_costs + transport_costs

        # --- KISITLAR ---
        
        # Kısıt 1: Her müşteri SADECE 1 depodan hizmet almalı
        for i in I:
            possible_depots = [j for j in J if (i,j) in valid_pairs]
            if possible_depots:
                prob += pulp.lpSum([x[(i,j)] for j in possible_depots]) == 1

        # Kısıt 2: Müşteri atanırsa depo açık olmalı
        for (i,j) in valid_pairs:
            prob += x[(i,j)] <= y[j]
            
        # Kısıt 3: Depo Kapasitesi
        for j in J:
            orders_assigned_to_j = [
                self.df_demand.loc[i, 'daily_orders'] * x[(i,j)] 
                for i in I if (i,j) in valid_pairs
            ]
            prob += pulp.lpSum(orders_assigned_to_j) <= self.df_sites.loc[j, 'capacity'] * y[j]

        # Kısıt 4: Maksimum açılacak depo sayısı
        prob += pulp.lpSum([y[j] for j in J]) <= max_stores_to_open
        
        # --- ÇÖZÜM ---
        # msg=0 logları kapatır, hata ayıklamak istersen 1 yapabilirsin
        prob.solve(pulp.PULP_CBC_CMD(msg=1, timeLimit=60))
        
        status = pulp.LpStatus[prob.status]
        print(f"✅ Çözüm Durumu: {status}")
        
        if status != 'Optimal':
            print("❌ Uygun çözüm bulunamadı!")
            return None

        # --- SONUÇLARI TOPARLA ---
        selected_sites = []
        for j in J:
            if y[j].varValue > 0.5:
                site_data = self.df_sites.loc[j].to_dict()
                site_data['is_selected'] = 1
                selected_sites.append(site_data)
        
        assignments = []
        for (i,j) in valid_pairs:
            if x[(i,j)].varValue > 0.5:
                assignments.append({
                    'customer_id': self.df_demand.loc[i, 'id'],
                    'assigned_site_id': self.df_sites.loc[j, 'site_id'],
                    'distance_km': dist_matrix[(i,j)]
                })
                
        df_results_sites = pd.DataFrame(selected_sites)
        df_results_assignments = pd.DataFrame(assignments)
        
        # Kaydet
        # self.df_demand_path kullanarak üst klasöre çıkıyoruz
        output_dir = os.path.join(os.path.dirname(self.df_demand_path), '../processed')
        # os.path.abspath ile yolun tam olduğundan emin olalım
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        df_results_sites.to_csv(os.path.join(output_dir, 'selected_sites.csv'), index=False)
        df_results_assignments.to_csv(os.path.join(output_dir, 'customer_assignments.csv'), index=False)
        
        total_cost = pulp.value(prob.objective)
        print(f"💰 Toplam Minimize Edilmiş Maliyet: {total_cost:,.2f} TL")
        print(f"🏭 Seçilen Depo Sayısı: {len(df_results_sites)}")
        
        return df_results_sites

# --- TEST BLOĞU ---
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d_path = os.path.join(base_dir, 'data', 'raw', 'demand_points.csv')
    s_path = os.path.join(base_dir, 'data', 'raw', 'candidate_sites.csv')
    
    optimizer = LogisticsOptimizer(d_path, s_path)
    optimizer.solve_model(max_stores_to_open=5)