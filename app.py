import stripe
import os
from flask import Flask, request
from flask_cors import CORS
from indexgenerator import make_index
from flask_mail import Mail, Message
from config import PASSWORD, SECRET_KEY

app = Flask(__name__)
CORS(app)

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='getyourindex@gmail.com',
    MAIL_PASSWORD=PASSWORD
)

mail = Mail(app)


@app.route('/<email>', methods=["POST"])
def send_index(email):
    ms = request.files['ms']
    words = request.files['words']

    message = 'here is your index'
    subject = "your index"
    make_index(ms, words)

    msg = Message(recipients=[email],
                  sender="getyourindex@gmail.com",
                  body=message,
                  subject=subject)

    with app.open_resource("index.txt") as fp:
        msg.attach("index.txt", "text/plain", fp.read())

    mail.send(msg)
    os.remove("index.txt")

    return {'result': "Hello World"}


# Set your secret key. Remember to switch to your live secret key in production!
# See your keys here: https://dashboard.stripe.com/account/apikeys
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
