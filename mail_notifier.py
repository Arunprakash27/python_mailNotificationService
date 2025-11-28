import os
from dotenv import load_dotenv
from flask import Flask,jsonify,request
from flask_mail import Mail,Message

load_dotenv()

app= Flask(__name__)

app.config["MAIL_SERVER"]= os.getenv("GMAIL_SERVER")
app.config["MAIL_PORT"]= os.getenv("GMAIL_PORT")
app.config["MAIL_USERNAME"] =os.getenv("GMAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("GMAIL_APP_PASSWORD")
app.config['MAIL_USE_SSL']= True

mail= Mail(app)

def store_to_database(request_json)->bool:
    return True

def send_email(recipient,first_name):

    message_body = f"Thank You {first_name} For Applying!\n After Careful reviewing your application, Our Team will Get Back To You!"

    gmessage=Message(subject= "Received Job Application",
            sender= app.config["MAIL_USERNAME"],
            recipients=[recipient],
            body= message_body
            )
    
    mail.send(message=gmessage)

@app.route("/submit",methods=["POST"])
def receive_details_send_mail():
    request_body = request.get_json()
    if not request_body:
        return jsonify("request body NOT FOUND"),404
    
    required_fields = [
        "first_name", "last_name", "email",
        "dob", "education_degree", "resume_pdf"
    ]

    missing = [f for f in required_fields if not request_body.get(f)]
    if missing:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing
        }), 400

    flag = store_to_database(request_body)
    first_name= request_body.get('')
    recipient = request_body.get('')
    if not flag:
        return jsonify("Error Sending mail"),500
    send_email(first_name,recipient)
    return jsonify("Your Application Accepted!\nCheck For Mail Confirmation")

if __name__ == "__main__":
    app.run()