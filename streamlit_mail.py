# app.py
import os
import base64
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import mysql.connector
import smtplib
from email.message import EmailMessage

load_dotenv()

# ---------------- CONFIG ----------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

MAIL_SERVER = os.getenv("GMAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("GMAIL_PORT", 465))
MAIL_USERNAME = os.getenv("GMAIL_USERNAME")
MAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # Gmail App Password

# ---------------- HELPERS ----------------
def encode_file_to_base64(uploaded_file):
    if uploaded_file is None:
        return None
    return base64.b64encode(uploaded_file.read()).decode("utf-8")

def clean_optional(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value != "" else None

def store_to_database(data) -> bool:
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

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
            data["first_name"],
            data["last_name"],
            data["email"],
            data["dob"],
            data["education_degree"],
            data.get("experience", 0),
            data.get("current_organization"),
            data.get("current_ctc"),
            data.get("expected_ctc"),
            data.get("notice_period"),
            data["resume_pdf"],  # BASE64 PDF
            datetime.now()
        )

        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        st.error(f"Database error: {e}")
        return False


def send_email(recipient, first_name):
   
    try:
        message_body = (
            f"Thank You {first_name} for applying!\n\n"
            "After reviewing your application, our team will get back to you soon."
        )

        msg = EmailMessage()
        msg["Subject"] = "Received Job Application"
        msg["From"] = MAIL_USERNAME
        msg["To"] = recipient
        msg.set_content(message_body)

        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as smtp:
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Email error: {e}")
        return False


st.set_page_config(page_title="Job Application", layout="centered")
st.title("Job Application Form")
st.markdown("Upload your details and resume")

with st.form("job_form"):
    col1, col2 = st.columns(2)

    with col1:
        first_name = st.text_input("First name")
        last_name = st.text_input("Last name")
        email = st.text_input("Email")
        dob = st.date_input("Date of birth")

    with col2:
        education_degree = st.selectbox(
            "Highest Education",
            ["High School", "Diploma", "Bachelor's", "Master's", "PhD", "Other"]
        )
        experience = st.number_input("Experience (years)", min_value=0, step=1)
        current_organization = st.text_input("Current organization")
        current_ctc = st.text_input("Current CTC")
        expected_ctc = st.text_input("Expected CTC")
        notice_period = st.text_input("Notice period")

    resume_pdf = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    submitted = st.form_submit_button("Submit Application")

if submitted:

    required = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "dob": dob,
        "education_degree": education_degree,
        "resume_pdf": resume_pdf
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        st.error(f"Missing required fields: {', '.join(missing)}")

    else:
        with st.spinner("Submitting your application..."):

            encoded_pdf = encode_file_to_base64(resume_pdf)

            data = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip(),
            "dob": dob.isoformat(),
            "education_degree": education_degree,
            "experience": int(experience),

            # Optional fields — converted to None if empty
            "current_organization": clean_optional(current_organization),
            "current_ctc": clean_optional(current_ctc),
            "expected_ctc": clean_optional(expected_ctc),
            "notice_period": clean_optional(notice_period),

            "resume_pdf": encoded_pdf,
        }

            # Save DB
            if store_to_database(data):
                st.success("Stored in database successfully!")

                # Email
                if send_email(email, first_name):
                    st.success("Confirmation email sent!")
                else:
                    st.warning("Saved, but email failed.")

            else:
                st.error("Database operation failed.")


with st.expander("Debug Info"):
    st.write("Mail:", MAIL_USERNAME)