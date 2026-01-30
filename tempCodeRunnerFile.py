from flask import Flask, jsonify, request,render_template
from flask_cors import CORS
from db_config import get_db_connection

app = Flask(__name__)
CORS(app)

# -------------------------
# 🩸 USERS CRUD
# -------------------------
@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Users ORDER BY User_ID;")
    users = cur.fetchall()
    cur.close()
    conn.close()

    columns = ['User_ID', 'Name', 'Contact_No', 'Blood_Group', 'Role']
    results = [dict(zip(columns, row)) for row in users]
    return jsonify(results)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Users (Name, Contact_No, Blood_Group, Role)
        VALUES (%s, %s, %s, %s)
        RETURNING User_ID;
    """, (data['Name'], data['Contact_No'], data['Blood_Group'], data['Role']))
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "User added successfully", "User_ID": user_id})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Users WHERE User_ID = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "User deleted successfully"})

# -------------------------
# 💉 DONATIONS CRUD
# -------------------------
@app.route('/donations', methods=['GET'])
def get_donations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Donations ORDER BY Donation_ID;")
    donations = cur.fetchall()
    cur.close()
    conn.close()

    columns = ['Donation_ID', 'Date', 'Quantity', 'Status', 'Donor_ID']
    results = [dict(zip(columns, row)) for row in donations]
    return jsonify(results)

@app.route('/donations', methods=['POST'])
def add_donation():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Donations (Date, Quantity, Status, Donor_ID)
        VALUES (%s, %s, %s, %s)
        RETURNING Donation_ID;
    """, (data['Date'], data['Quantity'], data['Status'], data['Donor_ID']))
    donation_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Donation recorded", "Donation_ID": donation_id})

# -------------------------
# 🩸 REQUESTS CRUD
# -------------------------
@app.route('/requests', methods=['GET'])
def get_requests():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Requests ORDER BY Request_ID;")
    requests_data = cur.fetchall()
    cur.close()
    conn.close()

    columns = ['Request_ID', 'Date', 'Required_Units', 'Status', 'Recipient_ID', 'Request_Type']
    results = [dict(zip(columns, row)) for row in requests_data]
    return jsonify(results)

@app.route('/requests', methods=['POST'])
def add_request():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Requests (Date, Required_Units, Status, Recipient_ID, Request_Type)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING Request_ID;
    """, (data['Date'], data['Required_Units'], data['Status'], data['Recipient_ID'], data['Request_Type']))
    request_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Request added", "Request_ID": request_id})

 # ---------------- HOSPITALS ----------------
@app.route('/hospitals', methods=['GET'])
def get_hospitals():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Hospitals")
    data = cur.fetchall()
    cur.close()
    conn.close()
    hospitals = [{"Org_ID": d[0], "Name": d[1], "Contact": d[2], "Location": d[3]} for d in data]
    return jsonify(hospitals)

@app.route('/hospitals', methods=['POST'])
def add_hospital():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Hospitals (Name, Contact, Location) VALUES (%s, %s, %s) RETURNING Org_ID",
                (data['Name'], data['Contact'], data['Location']))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Hospital added", "Org_ID": new_id})

# ---------------- APPOINTMENTS ----------------
@app.route('/appointments', methods=['GET'])
def get_appointments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Appointments")
    data = cur.fetchall()
    cur.close()
    conn.close()
    appointments = [{"Appointment_ID": d[0], "Date": str(d[1]), "Time_Slot": d[2], "Status": d[3], "User_ID": d[4]} for d in data]
    return jsonify(appointments)

@app.route('/appointments', methods=['POST'])
def add_appointment():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO appointments (Date, Time_Slot, Status, User_ID) VALUES (%s, %s, %s, %s) RETURNING Appointment_ID",
                (data['Date'], data['Time_Slot'], data['Status'], data['User_ID']))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Appointment added", "Appointment_ID": new_id})

# ---------------- TRANSACTIONS ----------------
@app.route('/transactions', methods=['GET'])
def get_transactions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Transactions")
    data = cur.fetchall()
    cur.close()
    conn.close()
    transactions = [{"Transaction_ID": d[0], "Date": str(d[1]), "Units_Allocated": d[2], "Method": d[3], "Request_ID": d[4], "Donation_ID": d[5]} for d in data]
    return jsonify(transactions)

@app.route('/transactions', methods=['POST'])
def add_transaction():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Transactions (Date, Units_Allocated, Method, Request_ID, Donation_ID) VALUES (%s, %s, %s, %s, %s) RETURNING Transaction_ID",
                (data['Date'], data['Units_Allocated'], data['Method'], data['Request_ID'], data['Donation_ID']))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Transaction added", "Transaction_ID": new_id})



# -------------------------
# 🩸 ROOT ENDPOINT
# -------------------------
@app.route('/')
def home():
    return jsonify({
        "message": "Blood Bank Management API is running 🚀",
        "endpoints": ["/users", "/donations", "/requests","/hospitals","/appointments","/transactions"]
    })
    
    
   
# Total donations per blood group
@app.route('/analytics/donations_by_blood_group')
def donations_by_blood_group():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.blood_type, SUM(d.quantity)
        FROM donations d
        JOIN users u ON d.donor_id = u.user_id
        JOIN inventory i ON i.blood_type = u.blood_group
        GROUP BY i.blood_type;
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# Monthly requests count
@app.route('/analytics/monthly_requests')
def monthly_requests():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT TO_CHAR(date, 'YYYY-MM') AS month, COUNT(*)
        FROM requests
        GROUP BY month
        ORDER BY month;
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
