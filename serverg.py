from flask import Flask, request, jsonify, session, redirect, render_template
import os
import pandas as pd
import sys

from preprocessing import preprocess_data
from qlearn import apply_dynamic_pricing


app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = "super_secret_key"
app.config['SESSION_PERMANENT'] = False

@app.before_request
def make_session_permanent():
    session.permanent = False
    if 'username' not in session and request.endpoint not in ('login', 'signup', 'static'):
        if request.endpoint not in ('static', 'favicon.ico'):
            if request.method == 'GET' and request.endpoint not in ('login', 'signup'):
                session.clear()


users = {}

os.makedirs('./uploads', exist_ok=True)
os.makedirs('./outputs', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check-auth')
def check_auth():
    return jsonify({'loggedIn': bool(session.get('username'))})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = users.get(uname)

        if user and user['password'] == pwd:
            session['username'] = uname
            return redirect('/')
        return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        uname = request.form['username']
        pwd = request.form['password']

        if uname in users:
            return "User already exists", 409

        users[uname] = {"email": email, "password": pwd}
        return redirect('/login')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/preprocess', methods=['POST'])
def preprocess():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    upload_path = os.path.join('./uploads', file.filename)
    file.save(upload_path)

    try:
        preprocess_data(upload_path)
        preview_df = pd.read_csv('./outputs/preprocessed_data.csv')

        # 🔥 Select only important columns
        preview_df = preview_df[['category_name', 'product_name', 'product_price', 'customer_id', 'customer_city']]

        preview_data = preview_df.head(20).to_dict(orient='records')  # still show 50 rows
        return jsonify({'success': True, 'preview': preview_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/qlearn', methods=['GET'])
def qlearn_route():
    try:
        apply_dynamic_pricing()
        optimized_data = pd.read_csv('./outputs/final_dynamic_pricing_grouped.csv')

        category_map = {}
        for category in optimized_data['category_name'].unique():
            group = optimized_data[optimized_data['category_name'] == category]
            products = group['product_name'].tolist()
            original_prices = group['product_price'].tolist()
            optimized_prices = group['optimized_price'].tolist()
            if len(products) > 0:  # ✅ Only include categories with at least 1 product
                category_map[category] = {
                    'products': products,
                    'original_prices': original_prices,
                    'optimized_prices': optimized_prices
                }

        return jsonify({
            'success': True,
            'categories': list(category_map.keys()),
            'category_map': category_map
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/kmeans', methods=['GET'])
def kmeans_route():
    try:
        clusters_data = pd.read_csv('./outputs/preprocessed_data.csv')

        product_names = clusters_data['product_name'].unique().tolist()
        product_map = {}

        for product in product_names:
            product_data = clusters_data[clusters_data['product_name'] == product]

            customers = []
            for _, row in product_data.iterrows():
                customers.append({
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'customer_city': row['customer_city']
                })

            if 1 < len(customers) < 15:  # ✅ Only products with less than 15 customers
                source_point = {
                    'latitude': product_data.iloc[0]['original_latitude'],
                    'longitude': product_data.iloc[0]['original_longitude']
                }

                product_map[product] = {
                    'source': source_point,
                    'customers': customers
                }

        sorted_products = sorted(product_map.keys())

        return jsonify({
            'success': True,
            'products': sorted_products,
            'product_map': product_map
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True, port=5000)
