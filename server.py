from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, sqlite3

app = Flask(__name__, static_folder="static")
CORS(app)

# PayPal Sandbox Keys
PAYPAL_CLIENT = "AVEpw1YnzsWsjh5briF9diZH5LCTjVrsafIgWkf8PSqcilNwtk-tuXmPDK2xR0YAb3uTi69CFeyjRsxW"
PAYPAL_SECRET = "EM1LaYMaMq1BOyoWPWl8dXAglHOrBsSfbeDeEdTLHvJ0P6GzyhctTnUrkcHg9GwqchU_2qYzNhOjjvJQ"
PAYPAL_OAUTH_API = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
PAYPAL_ORDER_API = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

Prijs_per_person = 1
DB_FILE = "reservations.db"

# --- إنشاء قاعدة البيانات وجدول إذا لم يكن موجود ---
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
            totaal REAL,
            betaling_status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_reservation(stad, datum, feest_naam, aantal_personen, namen, totaal, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reservations (stad, datum, feest_naam, aantal_personen, namen, totaal, betaling_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (stad, datum, feest_naam, aantal_personen, namen, totaal, status))
    conn.commit()
    conn.close()

# --- PayPal ---
def get_access_token():
    resp = requests.post(
        PAYPAL_OAUTH_API,
        auth=(PAYPAL_CLIENT, PAYPAL_SECRET),
        data={"grant_type": "client_credentials"}
    )
    return resp.json().get("access_token")

@app.route("/")
def home():
    return app.send_static_file("index.html")

@app.route("/reserveer", methods=["POST"])
def reserveer():
    data = request.get_json()

    stad = data.get("stad", "")
    datum = data.get("datum", "")
    feest_naam = data.get("feest_naam", "")
    aantal_personen = int(data.get("aantal_personen", 0))
    namen = data.get("namen", "")
    betalen = data.get("betalen", "").strip()  # ✅ تصحيح NoneType

    totaal = aantal_personen * Prijs_per_person

    if betalen.lower() != "ja":
        save_reservation(stad, datum, feest_naam, aantal_personen, namen, totaal, "geannuleerd")
        return jsonify({"status": "geannuleerd", "melding": "❌ Betaling geannuleerd."})

    # إنشاء عملية الدفع في PayPal
    access_token = get_access_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "EUR", "value": str(totaal)}}],
        "application_context": {
            "return_url": "http://127.0.0.1:5000/succes",
            "cancel_url": "http://127.0.0.1:5000/failed"
        }
    }

    resp = requests.post(PAYPAL_ORDER_API, json=payload, headers=headers)
    order = resp.json()

    if "links" not in order:
        return jsonify({"status": "fout", "melding": "PayPal fout: " + str(order)})

    approve_link = next(link["href"] for link in order["links"] if link["rel"] == "approve")

    # نسجل الحجز قبل الدفع
    save_reservation(stad, datum, feest_naam, aantal_personen, namen, totaal, "in_progress")

    return jsonify({"status": "redirect", "url": approve_link})

@app.route("/succes")
def succes():
    return app.send_static_file("succes.html")

@app.route("/failed")
def failed():
    return app.send_static_file("failed.html")

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
