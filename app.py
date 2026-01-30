# Updated app.py with the missing /admin/requests/<int:request_id> DELETE route
# This resolves the issue where deleting requests from the admin dashboard wasn't working.
# The frontend calls /admin/requests/<request_id> DELETE, but the route was missing in your code.
# I've added it below, integrated into your existing app.py structure.
# Also, ensure your database has the required views/tables (see notes at the end).

from flask import Flask, jsonify, request, render_template, redirect, session, url_for, abort
from db_config import get_db_connection  # Assume this returns a psycopg2 connection
import bcrypt
from flask_cors import CORS
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import date
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
def strftime_filter(value, format_spec='%Y-%m-%d'):
    if value is None:
        return ""
    return value.strftime(format_spec)
app.jinja_env.filters['strftime'] = strftime_filter

app.secret_key = os.environ.get('SECRET_KEY', 'my_secret_key')  # Use env var in prod
CORS(app)

# DB Context Manager (reduces boilerplate)
@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# Authentication Decorator (basic session-based; enhance with Flask-Login)
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                abort(401, "Login required")
            if role and session.get('role') != role:
                abort(403, "Role not authorized")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------
# 🩸 USERS CRUD (Standardized to lowercase schema)
# -------------------------
@app.route('/users', methods=['GET'])
def get_users():
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM users ORDER BY user_id;')
            users = cur.fetchall()
            columns = ['user_id', 'name', 'contact_no', 'blood_group', 'role', 'email', 'region']

            results = [dict(zip(columns, row)) for row in users]
            return jsonify(results)
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    if not all(k in data for k in ['name', 'contact_no', 'blood_group', 'role', 'email', 'password']):
        abort(400, "Missing required fields")
    
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (name, contact_no, blood_group, role, email, password)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING user_id;
            """, (data['name'], data['contact_no'], data['blood_group'], data['role'], data['email'], hashed_pw))
            user_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "User added successfully", "user_id": user_id}), 201
        except Exception as e:
            conn.rollback()
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required(role='Admin')  # Example: Restrict to admin
def delete_user(user_id):
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
            if cur.rowcount == 0:
                abort(404, "User not found")
            conn.commit()
            return jsonify({"message": "User deleted successfully"})
        except Exception as e:
            conn.rollback()
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# -------------------------
# 💉 DONATIONS CRUD
# -------------------------
@app.route('/donations', methods=['GET'])
def get_donations():
    donor_id = request.args.get('donor_id')  # Get query param, e.g., ?donor_id=123
    with get_db() as conn:
        cur = conn.cursor()
        try:
            query = "SELECT donation_id, date, quantity, status, donor_id FROM donations WHERE 1=1"
            params = []
            if donor_id:
                query += " AND donor_id = %s"
                params.append(donor_id)
            query += " ORDER BY date DESC;"  # Most recent first
            cur.execute(query, params)
            donations = cur.fetchall()
            columns = ['donation_id', 'date', 'quantity', 'status', 'donor_id']
            results = [dict(zip(columns, row)) for row in donations]
            return jsonify(results)
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

@app.route('/donations', methods=['POST'])
@login_required(role='Donor')
def add_donation():
    data = request.json
    if not all(k in data for k in ['date', 'quantity', 'status']):
        abort(400, "Missing required fields")
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO donations (date, quantity, status, donor_id)
                VALUES (%s, %s, %s, %s) RETURNING donation_id;
            """, (data['date'], data['quantity'], data['status'], session['user_id']))
            donation_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "Donation recorded", "donation_id": donation_id}), 201
        except Exception as e:
            conn.rollback()
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# -------------------------

# -------------------------
# Update /requests GET (lowercase schema, no quotes)
@app.route('/requests', methods=['GET'])
def get_requests():
    recipient_id = request.args.get('recipient_id')  # e.g., ?recipient_id=2
    with get_db() as conn:
        cur = conn.cursor()
        try:
            query = """
                SELECT request_id, date, required_units, status, recipient_id, 
                       request_type, blood_group 
                FROM requests WHERE 1=1
            """
            params = []
            if recipient_id:
                query += ' AND recipient_id = %s'
                params.append(recipient_id)
            query += ' ORDER BY date DESC;'  # Most recent first
            cur.execute(query, params)
            requests_data = cur.fetchall()
            results = []
            for row in requests_data:
                # Convert date to string for JSON serialization
                req_date = str(row[1]) if row[1] else None  # row[1] = date
                blood_group = row[6] if len(row) > 6 and row[6] else None  # blood_group (handle if missing)
                results.append({
                    'request_id': row[0],
                    'date': req_date,
                    'required_units': row[2],
                    'status': row[3],
                    'recipient_id': row[4],
                    'request_type': row[5],
                    'blood_group': blood_group
                })
            print(f"DEBUG: Fetched {len(results)} requests for recipient_id={recipient_id or 'all'}")  # Terminal debug
            return jsonify(results)
        except Exception as e:
            print(f"ERROR in /requests GET: {e}")  # Terminal debug
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# Update /requests POST (lowercase schema, no quotes)
@app.route('/requests', methods=['POST'])
@login_required(role='Recipient')  # Or add manual session check if no decorator
def add_request():
    data = request.json
    required_fields = ['date', 'required_units', 'request_type', 'blood_group']
    data['recipient_region'] = session.get('region')  # From user session (fetch on login)
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields: date, required_units, request_type, blood_group"}), 400
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
    INSERT INTO requests (date, required_units, status, recipient_id, recipient_region, request_type, blood_group)
    VALUES (%s, %s, 'Pending', %s, %s, %s, %s) RETURNING request_id;
""", (data['date'], data['required_units'], session['user_id'], data['recipient_region'], data['request_type'], data['blood_group']))
            request_id = cur.fetchone()[0]
            conn.commit()
            print(f"DEBUG: Created request {request_id} for user {session['user_id']}")  # Terminal debug
            return jsonify({"message": "Request added successfully", "request_id": request_id}), 201
        except Exception as e:
            conn.rollback()
            print(f"ERROR in /requests POST: {e}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            cur.close()



# ---------------- HOSPITALS ----------------
@app.route('/hospitals', methods=['GET'])
def get_hospitals():
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT org_id, name, contact, location FROM hospitals;")
            data = cur.fetchall()
            hospitals = [{"org_id": d[0], "name": d[1], "contact": d[2], "location": d[3]} for d in data]
            return jsonify(hospitals)
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

@app.route('/hospitals', methods=['POST'])
@login_required(role='Admin')
def add_hospital():
    data = request.get_json()
    if not all(k in data for k in ['name', 'contact', 'location']):
        abort(400, "Missing required fields")
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO hospitals (name, contact, location) VALUES (%s, %s, %s) RETURNING org_id",
                        (data['name'], data['contact'], data['location']))
            new_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "Hospital added", "org_id": new_id}), 201
        except Exception as e:
            conn.rollback()
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# ---------------- APPOINTMENTS (Merged duplicate POST) ----------------
@app.route('/appointments', methods=['GET'])
def get_appointments():
    user_id = request.args.get('user_id') or session.get('user_id') # Optional filter
    appointments = []
    with get_db() as conn:
        cur = conn.cursor()
        try:
            query = "SELECT appointment_id, date, time_slot, status, user_id FROM appointments WHERE 1=1"
            params = []
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            query += " ORDER BY date DESC, time_slot ASC;"
            cur.execute(query, params)
            data = cur.fetchall()
            for d in data:
                apt_date = str(d[1]) if d[1] else None
                apt_time_slot = str(d[2]) if d[2] else None
                appointments.append({
                    "appointment_id": d[0],
                    "date": apt_date,
                    "time_slot": apt_time_slot,
                    "status": d[3],
                    "user_id": d[4]
                })
            return render_template('appointments.html', appointments=appointments)
        except Exception as e:
            print(f"Full DB error: {e}")
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

@app.route('/appointments', methods=['POST'])
@login_required(role='Donor')
def add_appointment():
    data = request.get_json()
    if not all(k in data for k in ['date', 'time_slot']):
        abort(400, "Missing required fields")
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO appointments (date, time_slot, status, user_id) VALUES (%s, %s, 'Pending', %s) RETURNING appointment_id",
                        (data['date'], data['time_slot'], session['user_id']))
            new_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "Appointment added", "appointment_id": new_id}), 201
        except Exception as e:
            conn.rollback()
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# ---------------- TRANSACTIONS ----------------
@app.route('/transactions', methods=['GET'])
def get_transactions():
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT transaction_id, date, units_allocated, method, request_id, donation_id FROM transactions;")
            data = cur.fetchall()
            transactions = [{"transaction_id": d[0], "date": str(d[1]), "units_allocated": d[2], "method": d[3], "request_id": d[4], "donation_id": d[5]} for d in data]
            return jsonify(transactions)
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

@app.route('/transactions', methods=['POST'])
@login_required(role='Admin')
def add_transaction():
    data = request.get_json()
    if not all(k in data for k in ['date', 'units_allocated', 'method', 'request_id', 'donation_id']):
        abort(400, "Missing required fields")
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO transactions (date, units_allocated, method, request_id, donation_id) VALUES (%s, %s, %s, %s, %s) RETURNING transaction_id",
                        (data['date'], data['units_allocated'], data['method'], data['request_id'], data['donation_id']))
            new_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "Transaction added", "transaction_id": new_id}), 201
        except Exception as e:
            conn.rollback()
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()
            
# New route: GET /inventory (view stock)
@app.route('/inventory', methods=['GET'])
def get_inventory():
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute('SELECT blood_type, units FROM inventory_replica ORDER BY blood_type;')
            data = cur.fetchall()
            inventory = [{"blood_type": row[0], "units": row[1]} for row in data]
            return jsonify(inventory)
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

#----Admin routes
 # Admin Stats (Overview Cards)
@app.route('/admin/stats', methods=['GET'])
@login_required(role='Admin')  # Or manual check
def admin_stats():
    with get_db() as conn:
        cur = conn.cursor()
        try:
            # Total users (transparent from partitioned view)
            cur.execute("SELECT COUNT(*) FROM all_users;")
            total_users = cur.fetchone()[0]
            
            # Pending requests
            cur.execute("SELECT COUNT(*) FROM all_requests WHERE status = 'Pending';")
            pending_requests = cur.fetchone()[0]
            
            # Total donations (assume donations table exists; adjust query)
            cur.execute("SELECT COUNT(*) FROM donations;")  # Or SUM(quantity) if needed
            total_donations = cur.fetchone()[0]
            
            # Low stock (units < 10)
            cur.execute("SELECT COUNT(*) FROM inventory_replica WHERE units < 10;")
            low_stock = cur.fetchone()[0]
            
            return jsonify({
                "total_users": total_users,
                "pending_requests": pending_requests,
                "total_donations": total_donations,
                "low_stock": low_stock
            })
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# All Users (From Fragmented View)
@app.route('/admin/users', methods=['GET'])
@login_required(role='Admin')
def admin_users():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)  # Named access
        try:
            cur.execute("SELECT user_id, name, email, role, region, blood_group FROM all_users ORDER BY user_id;")
            users = cur.fetchall()
            return jsonify([dict(user) for user in users])  # List of dicts
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# All Requests (From Fragmented View)
@app.route('/admin/requests', methods=['GET'])
@login_required(role='Admin')
def admin_requests():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT request_id, date, blood_group, required_units, status, request_type, recipient_id 
                FROM all_requests ORDER BY date DESC;
            """)
            requests = cur.fetchall()
            return jsonify([dict(req) for req in requests])
        except Exception as e:
            abort(500, f"Database error: {str(e)}")
        finally:
            cur.close()

# Fulfill Request (Concurrency Demo: Lock + Deduct Inventory)
@app.route('/admin/fulfill/<int:request_id>', methods=['POST'])
@login_required(role='Admin')
def admin_fulfill_request(request_id):
    data = request.json or {}
    allocated_units = data.get('allocated_units', 0)  # From modal
    with get_db() as conn:
        cur = conn.cursor()
        try:
            # Start transaction with locking (concurrency control)
            cur.execute("BEGIN;")
            cur.execute("LOCK TABLE inventory_master IN EXCLUSIVE MODE;")
            cur.execute("LOCK TABLE requests IN EXCLUSIVE MODE;")
            
            
            # Get request details
            cur.execute("""
                SELECT blood_group, required_units, recipient_id FROM all_requests 
                WHERE request_id = %s FOR UPDATE;
            """, (request_id,))
            req = cur.fetchone()
            if not req:
            # Continuation of your app.py from the incomplete line: "conn" (after "if not req:")
# This completes the /admin/fulfill/<int:request_id> route and adds the rest of the file, including the new DELETE route for requests.

                conn.rollback()
                return jsonify({"error": "Request not found"}), 404
            
            blood_group, required_units, recipient_id = req
            units_to_deduct = allocated_units or required_units  # Use provided or full
            
            # Check stock
            cur.execute("SELECT units FROM inventory_master WHERE blood_type = %s FOR UPDATE;", (blood_group,))
            stock_row = cur.fetchone()
            if not stock_row or stock_row[0] < units_to_deduct:
                conn.rollback()
                return jsonify({"error": "Insufficient stock"}), 400
            
            # Deduct stock (replication transparency: Update master)
            cur.execute("""
                UPDATE inventory_master SET units = units - %s, last_updated = CURRENT_TIMESTAMP 
                WHERE blood_type = %s;
            """, (units_to_deduct, blood_group))
            
            # Update request status
            cur.execute("""
                UPDATE requests SET status = 'Fulfilled' WHERE request_id = %s;
            """, (request_id,))
            
            conn.commit()
            print(f"DEBUG: Fulfilled request {request_id}: Deducted {units_to_deduct} from {blood_group}")
            return jsonify({"message": f"Request {request_id} fulfilled. Deducted {units_to_deduct} units from {blood_group} stock."})
        except Exception as e:
            conn.rollback()
            print(f"ERROR fulfilling request: {e}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            cur.close()

# Update Inventory (Write to Master)
@app.route('/admin/inventory', methods=['POST'])
@login_required(role='Admin')
def admin_update_inventory():
    data = request.json
    blood_type = data.get('blood_type')
    new_units = data.get('new_units')
    if not blood_type or new_units is None:
        return jsonify({"error": "Missing blood_type or new_units"}), 400
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory_master SET units = %s, last_updated = CURRENT_TIMESTAMP 
                WHERE blood_type = %s;
            """, (new_units, blood_type))
            if cur.rowcount == 0:
                # Insert if not exists
                cur.execute("""
                    INSERT INTO inventory_master (blood_type, units) VALUES (%s, %s);
                """, (blood_type, new_units))
            conn.commit()
            return jsonify({"message": f"Updated {blood_type} to {new_units} units."})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            cur.close()

# Manage Privileges (Grant/Revoke SQL Execution)
@app.route('/admin/privileges', methods=['POST'])
@login_required(role='Admin')
def admin_privileges():
    data = request.json
    action = data.get('action')  # 'grant' or 'revoke'
    privilege = data.get('privilege')  # 'SELECT', etc.
    table = data.get('table')  # 'all_requests', etc.
    target_role = data.get('role')  # 'donor_role'
    if not all([action, privilege, table, target_role]):
        return jsonify({"error": "Missing parameters"}), 400
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cmd = f"{action.upper()} {privilege} ON {table} TO {target_role};"
            cur.execute(cmd)
            conn.commit()
            print(f"DEBUG: Executed privilege command: {cmd}")  # Log for demo
            return jsonify({"message": f"Executed: {cmd}"})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"SQL error: {str(e)} (Check table/role names)"}), 500
        finally:
            cur.close()

# Delete User
@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required(role='Admin')
def admin_delete_user(user_id):
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "User not found"}), 404
            conn.commit()
            return jsonify({"message": f"User {user_id} deleted."})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)} (FK constraints?)"}), 500
        finally:
            cur.close()

# Update User Role/Region
@app.route('/admin/users/<int:user_id>', methods=['PUT'])
@login_required(role='Admin')
def admin_update_user(user_id):
    data = request.json
    new_role = data.get('role')
    new_region = data.get('region')
    if not new_role or not new_region:
        return jsonify({"error": "Missing role or region"}), 400
    
    with get_db() as conn:
        cur = conn.cursor()
        try:
            # Update (PG routes to correct partition based on new_region)
            cur.execute("""
                UPDATE users SET role = %s, region = %s WHERE user_id = %s;
            """, (new_role, new_region, user_id))
            if cur.rowcount == 0:
                return jsonify({"error": "User not found"}), 404
            conn.commit()
            return jsonify({"message": f"Updated user {user_id}: Role={new_role}, Region={new_region}"})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            cur.close()

# Delete Request (Added this route to fix the "deleting requests" issue)
@app.route('/admin/requests/<int:request_id>', methods=['DELETE'])
@login_required(role='Admin')
def admin_delete_request(request_id):
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM requests WHERE request_id = %s;", (request_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "Request not found"}), 404
            conn.commit()
            return jsonify({"message": f"Request {request_id} deleted."})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            cur.close()

# ===========================
# USER LOGIN & LOGOUT ROUTES
# ===========================
from psycopg2.extras import RealDictCursor  # Add this import if using DictCursor (optional but recommended)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Missing email or password"}), 400
        
        email = data['email']
        password = data['password']
        with get_db() as conn:  # If using RealDictCursor, update get_db_connection to return cursor_factory=RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)  # Named dict access (optional; fallback to tuple below)
            try:
                # Fetch all columns to access region (index 7: user_id=0, name=1, contact_no=2, blood_group=3, role=4, email=5, password=6, region=7)
                cur.execute("""
                    SELECT user_id, name, contact_no, blood_group, role, email, password, region 
                    FROM users WHERE email = %s;
                """, (email,))
                user = cur.fetchone()
                
                if user:
                    # If using DictCursor: user = {'user_id': 1, 'region': 'North', ...}
                    # If tuple: Access by index
                    if isinstance(user, dict):
                        user_dict = user
                    else:
                        user_dict = {
                            'user_id': user[0], 'name': user[1], 'contact_no': user[2], 
                            'blood_group': user[3], 'role': user[4], 'email': user[5], 
                            'password': user[6], 'region': user[7]
                        }
                    
                    if bcrypt.checkpw(password.encode('utf-8'), user_dict['password'].encode('utf-8')):
                        session['user_id'] = user_dict['user_id']
                        session['name'] = user_dict['name']
                        session['role'] = user_dict['role']
                        session['region'] = user_dict['region'] or 'North'  # Default if NULL
                        print(f"DEBUG: Login successful for {email}, region: {session['region']}")  # Optional log
                        return jsonify({
                            "message": "Login successful", 
                            "role": user_dict['role'],
                            "region": session['region']  # Optional: Return for frontend
                        }), 200
                    else:
                        return jsonify({"error": "Invalid credentials"}), 401
                else:
                    return jsonify({"error": "Invalid credentials"}), 401
            except Exception as e:
                print(f"Login DB Error: {e}")  # Log for debug
                return jsonify({"error": "Server error. Please try again."}), 500
            finally:
                cur.close()
    
    # GET: Render template
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    # Default region if not provided (for demo)
    data['region'] = data.get('region', 'North')
    
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (name, contact_no, blood_group, role, email, password, region)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING user_id;
            """, (data['name'], data['contact_no'], data['blood_group'], data['role'], 
                  data['email'], hashed_pw, data['region']))
            user_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "User registered", "user_id": user_id, "region": data['region']}), 201
        except Exception as e:
            conn.rollback()
            abort(500, f"Database error: {str(e)}")
            
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')


@app.route('/dashboard')
@login_required()  # Or without role for general access
def dashboard():
    return render_template('index.html')

@app.route('/donor_dashboard')
@login_required(role='Donor')
def donor_dashboard():
    if 'role' not in session or session['role'] != 'Donor':
        return redirect(url_for('login'))
    return render_template('donor_dashboard.html', 
                          name=session['name'], 
                          user_id=session['user_id'])
    

@app.route('/recipient_dashboard')
@login_required(role='Recipient')  # If using decorator
def recipient_dashboard():
    if 'role' not in session or session['role'] != 'Recipient':
        return redirect(url_for('login'))
    
    today_date = date.today().isoformat()  # e.g., '2023-10-11'
    return render_template('recipient_dashboard.html', 
                          name=session['name'], 
                          user_id=session['user_id'],
                          today_date=today_date) 
    
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # Role check (manual; or use @login_required(role='Admin') if you have the decorator)
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))  # Or abort(403, "Admin access required")
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('admin_dashboard.html', 
                          name=session['name'], 
                          user_id=session['user_id'])
    
   

# -------------------------
# 🩸 ROOT ENDPOINT
# -------------------------
@app.route('/')
def home():
    return jsonify({
        "message": "Blood Bank Management API is running 🚀",
        "endpoints": ["/users", "/donations", "/requests", "/hospitals","/appointments","/transactions","/inventory"]
    })

if __name__ == '__main__':
    app.run(debug=True)
