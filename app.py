import stripe
import os
import random
import string
from flask import Flask, request
from flask_cors import CORS
from indexgenerator import make_index
from flask_mail import Mail, Message
from worker import conn
from rq import Queue

# from config import PASSWORD, SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY')
PASSWORD = os.environ.get('PASSWORD')


app = Flask(__name__)
CORS(app)

q = Queue(connection=conn)

app.config.update(
    MAIL_SERVER='smtp.zoho.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,  
    SECURITY_EMAIL_SENDER='getyourindex@zohomail.com',
    MAIL_USERNAME='getyourindex@zohomail.com',
    MAIL_PASSWORD=PASSWORD
)

mail = Mail(app)


def make_and_send(ms_path, words_path, email):
    print("***words_path", words_path)
    with open(words_path) as words:
        with app.app_context():

            message = 'here is your index'
            subject = 'your index'
            make_index(ms_path, words)
            msg = Message(recipients=[email],
                        sender="getyourindex@zohomail.com",
                        body=message,
                        subject=subject)

            with app.open_resource("index.txt") as fp:
                msg.attach("index.txt", "text/plain", fp.read())

            mail.send(msg)

            os.remove(ms_path)
            os.remove(words_path)
            os.remove("index.txt")
        return app

@app.route('/<email>', methods=["POST"])
def send_index(email):
    ms = request.files['ms']
    words = request.files['words']
    print("*******checking werkzeug fileresource", ms)
    
    cwd = os.getcwd()

    letters = string.ascii_lowercase
    random_path_ms = ''.join(random.choice(letters) for i in range(5))
    random_path_words = ''.join(random.choice(letters) for i in range(5))
    print("******cwd", cwd)
    # ms_path = os.path.join(cwd, f"{random_path_ms}.pdf")
    # words_path = os.path.join(cwd, f"{random_path_words}.txt")
    ms_path = os.path.join("/tmp", f"{random_path_ms}.pdf")
    words_path = os.path.join("/tmp", f"{random_path_words}.txt")
    print("********ms_path", ms_path)
    ms.save(ms_path)
    words.save(words_path)
    q.enqueue(make_and_send, ms_path, words_path, email)
    
    return {'result': "success"}


stripe.api_key = SECRET_KEY


@app.route('/pay', methods=['POST'])
def pay():
    email = request.json.get('email')
    amt = request.json.get('amount')
    amt = (int(amt) * 100)

    if not email or not amt:
        return 'please submit valid email and amount', 400

    intent = stripe.PaymentIntent.create(
        amount=amt,
        currency='usd',
        payment_method_types=['card'],
        receipt_email=email,
    )

    return {'client_secret': intent['client_secret']}