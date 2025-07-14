import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os
from tqdm import tqdm

def perform_kmeans(input_csv_path, output_csv_path='./outputs/final_route_clusters.csv'):
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    
    data = pd.read_csv(input_csv_path)
    required_cols = ['original_latitude', 'original_longitude', 'latitude', 'longitude']
    data.dropna(subset=required_cols, inplace=True)

    dept_scaler = StandardScaler()
    data[['scaled_dept_latitude', 'scaled_dept_longitude']] = dept_scaler.fit_transform(data[['original_latitude', 'original_longitude']])

    order_scaler = StandardScaler()
    order_scaled = order_scaler.fit_transform(data[['latitude', 'longitude']])
    data['scaled_order_lat'] = order_scaled[:, 0]
    data['scaled_order_lon'] = order_scaled[:, 1]

    total_routes = []

    for dept, group in tqdm(data.groupby('department_name'), desc='Clustering by Department'):
        unique_coords = group[['scaled_dept_latitude', 'scaled_dept_longitude']].drop_duplicates()
        n_clusters = len(unique_coords)
        if n_clusters < 2:
            continue

        kmeans = KMeans(n_clusters=n_clusters, init=unique_coords.to_numpy(), n_init=1, random_state=42)
        group = group.copy()
        group['cluster'] = kmeans.fit_predict(group[['scaled_dept_latitude', 'scaled_dept_longitude']])

        real_centers = dept_scaler.inverse_transform(kmeans.cluster_centers_)
        group['cluster_center_lat'] = group['cluster'].map({i: real_centers[i][0] for i in range(n_clusters)})
        group['cluster_center_lon'] = group['cluster'].map({i: real_centers[i][1] for i in range(n_clusters)})

        order_coords = group[['scaled_order_lat', 'scaled_order_lon']].to_numpy()
        centers = kmeans.cluster_centers_
        dists = np.linalg.norm(order_coords[:, None, :] - centers[None, :, :], axis=2)
        group['assigned_cluster'] = np.argmin(dists, axis=1)
        group['euclidean_distance'] = np.min(dists, axis=1)

        total_routes.append(group)

    final_routes = pd.concat(total_routes)

    out_columns = [
        'customer_id', 'department_name', 'original_latitude', 'original_longitude',
        'order_city', 'order_country', 'order_state', 'latitude', 'longitude',
        'cluster', 'assigned_cluster', 'euclidean_distance',
        'cluster_center_lat', 'cluster_center_lon'
    ]
    out_columns = [col for col in out_columns if col in final_routes.columns]

    final_routes[out_columns].to_csv(output_csv_path, index=False)
    print(f"✅ Final clustered routes saved to {output_csv_path}")

if __name__ == "__main__":
    perform_kmeans('./outputs/preprocessed_route_data.csv')
