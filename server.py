from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os, requests

app = Flask(__name__)
CORS(app)  # يسمح بطلبات من أي دومين، يمكنك تقييدها لاحقًا

# --- قاعدة البيانات ---
DB_FILE = os.path.join(os.path.dirname(__file__), "reservations.db")
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stad TEXT,
            datum TEXT,
            feest_naam TEXT,
            aantal_personen INTEGER,
            namen TEXT,
            customer_email TEXT,
            totaal REAL,
            betaling_status TEXT
        )
    ''')
    conn.commit()
    conn.close()
init_db()

def save_reservation(stad, datum, feest_naam, aantal_personen, namen, email, totaal, status):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO reservations (stad, datum, feest_naam, aantal_personen, namen, customer_email, totaal, betaling_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (stad, datum, feest_naam, aantal_personen, namen, email, totaal, status))
        conn.commit()
    finally:
        conn.close()

# --- إعدادات الدفع (PayPal مثال) ---
PAYPAL_CLIENT = "AVEpw1YnzsWsjh5briF9diZH5LCTjVrsafIgWkf8PSqcilNwtk-tuXmPDK2xR0YAb3uTi69CFeyjRsxW"
PAYPAL_SECRET = "EM1LaYMaMq1BOyoWPWl8dXAglHOrBsSfbeDeEdTLHvJ0P6GzyhctTnUrkcHg9GwqchU_2qYzNhOjjvJQ"
PAYPAL_OAUTH_API = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
PAYPAL_ORDER_API = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

# --- Routes ---
@app.route("/reserveer", methods=["POST"])
def reserveer():
    try:
        data = request.get_json() or {}
        stad = data.get("stad","")
        datum = data.get("datum","")
        feest_naam = data.get("feest_naam","")
        try:
            aantal_personen = int(data.get("aantal_personen",0))
        except:
            aantal_personen = 0
        namen = data.get("namen","")
        customer_email = (data.get("customer_email") or "").strip()
        totaal = aantal_personen * 150  # سعر ثابت

        # حفظ كـ in_progress
        save_reservation(stad, datum, feest_naam, aantal_personen, namen, customer_email, totaal, "in_progress")

        # --- PayPal ---
        auth_resp = requests.post(
            PAYPAL_OAUTH_API,
            auth=(PAYPAL_CLIENT,PAYPAL_SECRET),
            data={"grant_type":"client_credentials"}
        )
        auth_resp.raise_for_status()
        token = auth_resp.json().get("access_token")

        headers = {"Content-Type":"application/json","Authorization":f"Bearer {token}"}
        payload = {
            "intent": "CAPTURE",
            "purchase_units":[{"amount":{"currency_code":"EUR","value":str(totaal)}}],
            "application_context":{
                "return_url":"https://yourusername.pythonanywhere.com/succes",
                "cancel_url":"https://yourusername.pythonanywhere.com/failed"
            }
        }
        order_resp = requests.post(PAYPAL_ORDER_API,json=payload,headers=headers)
        order_resp.raise_for_status()
        order = order_resp.json()
        approve_link = next((link["href"] for link in order.get("links",[]) if link.get("rel")=="approve"), None)

        if approve_link:
            return jsonify({"status":"redirect","url":approve_link})
        return jsonify({"status":"fout","melding":"Geen link PayPal ontvangen."})

    except Exception as e:
        print("Error /reserveer:", e)
        return jsonify({"status":"fout","melding":"Server error"})

@app.route("/succes")
def succes():
    return app.send_static_file("succes.html")

@app.route("/failed")
def failed():
    return app.send_static_file("failed.html")

if __name__ == "__main__":
    import os
    if os.environ.get("PYTHONANYWHERE") is None:
        app.run(debug=True, port=5001)  # تشغيل محلي بدون تعارض
