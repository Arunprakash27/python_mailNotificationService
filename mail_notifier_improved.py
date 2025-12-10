import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_mail import Mail, Message
import mysql.connector

load_dotenv()

app = Flask(__name__)

# ---------------- MAIL CONFIG ----------------
app.config["MAIL_SERVER"] = os.getenv("GMAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("GMAIL_PORT"))
app.config["MAIL_USERNAME"] = os.getenv("GMAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("GMAIL_APP_PASSWORD")
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)

# ---------------- DATABASE CONFIG ----------------
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# ---------------- DATABASE FUNCTION ----------------
def store_to_database(data) -> bool:
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        sql = """
        INSERT INTO job_applications
        (
            first_name, last_name, email, dob,
            education_degree, experience,
            current_organization, current_ctc,
            expected_ctc, notice_period,
            resume_pdf, created_at
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            data.get("first_name"),
            data.get("last_name"),
            data.get("email"),
            data.get("dob"),
            data.get("education_degree"),
            data.get("experience", 0),
            data.get("current_organization"),
            data.get("current_ctc"),
            data.get("expected_ctc"),
            data.get("notice_period"),
            data.get("resume_pdf"),
            datetime.now()
        )

        cursor.execute(sql, values)
        connection.commit()

        cursor.close()
        connection.close()
        return True

    except Exception as e:
        print("DB Error:", e)
        return False

# ---------------- EMAIL FUNCTION ----------------
def send_email(recipient, first_name):
    message_body = (
        f"Thank You {first_name} for applying!\n\n"
        "After carefully reviewing your application, "
        "our team will get back to you soon."
    )
    print(f"{recipient}-{first_name}")
    
    gmessage = Message(
        subject="Received Job Application",
        sender=app.config["MAIL_USERNAME"],
        recipients=[recipient],
        body=message_body
    )

    mail.send(gmessage)

# ---------------- API ENDPOINT ----------------
@app.route("/submit", methods=["POST"])
def receive_details_send_mail():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body not found"}), 400

    required_fields = [
        "first_name", "last_name", "email",
        "dob", "education_degree", "resume_pdf"
    ]

    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing
        }), 400
    
    print("Passed Validation")

    if not store_to_database(data):
        return jsonify({"error": "Database error"}), 500

    print("stored to database")

    send_email(
        recipient=data.get("email"),
        first_name=data.get("first_name")
    )

    return jsonify({
        "message": "Application accepted! Check your email for confirmation."
    }), 200


if __name__ == "__main__":
    app.run(debug=True)
