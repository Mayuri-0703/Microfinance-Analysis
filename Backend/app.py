from flask import Flask, render_template, request, url_for, redirect, flash, jsonify
import pandas as pd
import pickle
import mysql.connector
import numpy as np
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "Mayuri_2004")

# Load ML models & scaler
try:
    with open('models/loan_eligibility.pkl', 'rb') as model_file:
        eligibility_model = pickle.load(model_file)
    with open('models/loan_prediction.pkl', 'rb') as loan_model_file:
        loan_model = pickle.load(loan_model_file)
    with open('models/scaler.pkl', 'rb') as scaler_file:
        scaler = pickle.load(scaler_file)
except Exception as e:
    print("Error loading ML models:", str(e))

# MySQL Database Connection
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mayuri@0727",
        database="microfinance_db"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS eligible_candidates (
        Vendor_No VARCHAR(20) PRIMARY KEY,
        Business_Type VARCHAR(50),
        PAN_Card VARCHAR(20),
        Aadhaar_Card VARCHAR(20),
        Total_Earnings FLOAT,
        Income_StdDev FLOAT
    )''')
    conn.commit()
except mysql.connector.Error as err:
    print("Database connection error:", err)

@app.route('/')
def home():
    return render_template('bank.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/Educational_Resources')
def Educational_Resources():
    return render_template('educational_resources.html')

@app.route('/check-eligibility')
def check_eligibility():
    return render_template('check_eligibility.html')

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    try:
        df = pd.read_csv(file)
        required_columns = {"Vendor_No", "Business_Type", "Total_Earnings", "Income_StdDev", "PAN_Card", "Aadhaar_Card"}
        if not required_columns.issubset(df.columns):
            return jsonify({'error': 'CSV file is missing required columns!'})
        
        features = df[['Total_Earnings', 'Income_StdDev']]
        features_scaled = scaler.transform(features)
        df['Eligibility'] = eligibility_model.predict(features_scaled)
        eligible = df[df['Eligibility'] == 1]
        eligible_count = len(eligible)
        non_eligible_count = len(df) - eligible_count
        
        for _, row in eligible.iterrows():
            cursor.execute('''INSERT INTO eligible_candidates (Vendor_No, Business_Type, PAN_Card, Aadhaar_Card, Total_Earnings, Income_StdDev)
                              VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE 
                              Business_Type=VALUES(Business_Type), PAN_Card=VALUES(PAN_Card), Aadhaar_Card=VALUES(Aadhaar_Card), 
                              Total_Earnings=VALUES(Total_Earnings), Income_StdDev=VALUES(Income_StdDev)''',
                           (row['Vendor_No'], row['Business_Type'], row['PAN_Card'], row['Aadhaar_Card'], row['Total_Earnings'], row['Income_StdDev']))
        conn.commit()
        
        eligible_list = eligible.to_dict(orient='records')
        return render_template('eligibility_result.html', eligible=eligible_list, eligible_count=eligible_count, non_eligible_count=non_eligible_count)
    except Exception as e:
        return jsonify({'error': f"Error processing file: {str(e)}"})

@app.route('/loan_prediction_form')
def loan_prediction_form():
    return render_template('loan_prediction.html')

@app.route('/loan_prediction', methods=['GET', 'POST'])
def loan_prediction():
    if request.method == 'POST':
        vendor_no = request.form.get('vendor_no')
        business_type = request.form.get('business_type')
        pan_card = request.form.get('pan_card')
        total_earnings = request.form.get('total_earnings')
        income_stddev = request.form.get('income_stddev')

        if not vendor_no or not pan_card or not total_earnings or not income_stddev:
            return jsonify({"error": "Please fill all fields!"})

        try:
            total_earnings = float(total_earnings)
            income_stddev = int(float(income_stddev))  # Take only integer part
        except ValueError:
            return jsonify({"error": "Invalid numerical values!"})

        # Check if Vendor exists in eligible_candidates
        cursor.execute('''SELECT Business_Type, PAN_Card, Total_Earnings, Income_StdDev 
                          FROM eligible_candidates WHERE Vendor_No = %s''', (vendor_no,))
        user_data = cursor.fetchone()

        if not user_data:
            return jsonify({'error': 'Vendor number is incorrect. Please enter a valid vendor number.'})

        db_business_type, db_pan_card, db_total_earnings, db_income_stddev = user_data

        # Extract only the integer part of the database value
        db_income_stddev = int(db_income_stddev)

        # Check for mismatches
        if business_type.lower() != db_business_type.lower():
            return jsonify({'error': f"Business Type mismatch. Expected: {db_business_type}"})
        if pan_card.upper() != db_pan_card.upper():
            return jsonify({'error': "Invalid PAN number. Please enter the correct PAN."})
        if total_earnings != db_total_earnings:
            return jsonify({'error': f"Total Earnings mismatch. Expected: {db_total_earnings}"})
        if income_stddev != db_income_stddev:
            return jsonify({'error': f"Income StdDev mismatch. Expected: {db_income_stddev}"})

        # Predict Loan Amount
        predicted_loan_amount = loan_model.predict([[total_earnings, income_stddev]])[0]

        return jsonify({"loan_amount": round(predicted_loan_amount, 2)})

    return render_template('loan_prediction.html')

if __name__ == '__main__':
    app.run(debug=True)



