import numpy as np
import pandas as pd
import random
import os

class QLearning:
    def __init__(self, states, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.states = states
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = np.zeros((len(states), len(actions)))

    def choose_action(self, state_idx):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(range(len(self.actions)))
        return np.argmax(self.q_table[state_idx])

    def update_q(self, state_idx, action_idx, reward, next_state_idx):
        best_next_action = np.argmax(self.q_table[next_state_idx])
        td_target = reward + self.gamma * self.q_table[next_state_idx][best_next_action]
        td_error = td_target - self.q_table[state_idx][action_idx]
        self.q_table[state_idx][action_idx] += self.alpha * td_error

def apply_dynamic_pricing(input_path='./outputs/preprocessed_data.csv', output_path='./outputs/final_dynamic_pricing_grouped.csv'):
    os.makedirs('./outputs', exist_ok=True)

    # Load preprocessed data
    data = pd.read_csv(input_path)

    # Load mapping: product_name ➔ category_name
    mapping_df = pd.read_csv('./outputs/product_category_mapping.csv')
    product_to_category = dict(zip(mapping_df['product_name'], mapping_df['category_name']))

    grouped_data = data.groupby('product_name').agg({
        'product_category_id': 'first',
        'product_price': 'mean',
        'order_item_quantity': 'sum',
        'sales': 'sum',
        'order_item_profit_ratio': 'mean',
        'profit_per_order': 'sum',
        'order_profit_per_order': 'sum'
    }).reset_index()

    actions = [0.85, 0.95, 1.0, 1.05, 1.15]
    states = list(grouped_data['product_category_id'].unique())
    state_to_idx = {state: idx for idx, state in enumerate(states)}
    q_model = QLearning(states, actions)

    # Attach category_name using mapping
    grouped_data['category_name'] = grouped_data['product_name'].map(product_to_category)

    for idx, row in grouped_data.iterrows():
        try:
            state = row['product_category_id']
            state_idx = state_to_idx[state]

            action_idx = q_model.choose_action(state_idx)
            price_multiplier = actions[action_idx]
            new_price = row['product_price'] * price_multiplier

            base_profit = row['order_profit_per_order']
            sales_adjustment = row['sales'] * price_multiplier
            margin_bonus = row['order_item_profit_ratio'] * 10
            penalty = 50 if price_multiplier > 1.05 and row['sales'] < 1000 else 0

            reward = base_profit + sales_adjustment + margin_bonus - penalty

            q_model.update_q(state_idx, action_idx, reward, state_idx)

            grouped_data.at[idx, 'optimized_price'] = round(new_price, 2)
            grouped_data.at[idx, 'price_action'] = price_multiplier
            grouped_data.at[idx, 'reward'] = reward

            optimized_margin = (new_price - row['product_price']) / new_price
            grouped_data.at[idx, 'optimized_margin'] = round(optimized_margin, 4)

        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            continue

    structured_data = grouped_data[[
        'product_category_id', 'category_name', 'product_name', 'product_price', 'optimized_price',
        'order_item_quantity', 'sales', 'price_action', 'reward',
        'order_item_profit_ratio', 'profit_per_order', 'order_profit_per_order', 'optimized_margin'
    ]]

    structured_data.to_csv(output_path, index=False)
    print(f"✅ Optimized pricing saved to {output_path}")

if __name__ == "__main__":
    apply_dynamic_pricing()
