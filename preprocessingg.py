import pandas as pd
import os

def preprocess_data(input_path='./uploads/order_locations_with_photon_coords1.csv', output_path='./outputs/preprocessed_data.csv'):
    os.makedirs('./outputs', exist_ok=True)

    data = pd.read_csv(input_path)

    # Fill missing values
    fill_values = {
        'payment_type': 'Unknown',
        'customer_city': 'Unknown',
        'customer_country': 'Unknown',
        'customer_state': 'Unknown',
        'order_state': 'Unknown',
        'order_city': 'Unknown',
        'order_country': 'Unknown',
        'order_status': 'Unknown',
        'shipping_mode': 'Unknown',
        'category_name': 'Unknown',
        'department_name': 'Unknown',
        'market': 'Unknown',
        'label': 'Unknown'
    }
    data.fillna(value=fill_values, inplace=True)

    numeric_columns = [
        'profit_per_order', 'sales_per_customer', 'order_item_discount',
        'order_item_discount_rate', 'order_item_product_price',
        'order_item_profit_ratio', 'order_item_quantity',
        'sales', 'order_item_total_amount', 'order_profit_per_order',
        'product_price', 'latitude', 'longitude',
        'original_latitude', 'original_longitude'
    ]
    data[numeric_columns] = data[numeric_columns].fillna(0)

    data.to_csv(output_path, index=False)

    # Save product_name ➔ category_name mapping
    mapping = data[['product_name', 'category_name']].drop_duplicates()
    mapping.to_csv('./outputs/product_category_mapping.csv', index=False)

    print(f"✅ Preprocessing complete! Saved to {output_path}")
    print(f"✅ Mapping saved to ./outputs/product_category_mapping.csv")

if __name__ == "__main__":
    preprocess_data()
