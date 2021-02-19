import stripe
import os
import random
import string
import boto3
from flask import Flask, request
from flask_cors import CORS
from indexgenerator import make_index
from flask_mail import Mail, Message
from worker import conn
from rq import Queue

# from config import PASSWORD, SECRET_KEY, S3_BUCKET, S3_KEY, S3_SECRET
SECRET_KEY = os.environ.get('SECRET_KEY')
PASSWORD = os.environ.get('PASSWORD')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_KEY = os.environ.get('S3_KEY')
S3_SECRET = os.environ.get('S3_SECRET')

s3 = boto3.client(
    's3',
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET)

s3_resource = boto3.resource('s3')
my_bucket = s3_resource.Bucket(S3_BUCKET)

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


def make_and_send(ms_name, words_name, email):

    with app.app_context():
        s3.download_file(S3_BUCKET, ms_name, ms_name)
        s3.download_file(S3_BUCKET, words_name, words_name)

        with open(words_name) as words:
            make_index(ms_name, words)

        msg = Message(recipients=[email],
                    sender="getyourindex@zohomail.com",
                    body='here is your index',
                    subject='your index')

        with app.open_resource("index.txt") as fp:
            msg.attach("index.txt", "text/plain", fp.read())

        mail.send(msg)

        os.remove(ms_name)
        os.remove(words_name)
        os.remove("index.txt")
        return app

@app.route('/<email>', methods=["POST"])
def send_index(email):
    ms = request.files['ms']
    words = request.files['words']

    letters = string.ascii_lowercase
    random_name = ''.join(random.choice(letters) for i in range(5))
    ms.filename = f"{random_name}.pdf"
    words.filename = f"{random_name}.txt"

    my_bucket.Object(ms.filename).put(Body=ms)
    my_bucket.Object(words.filename).put(Body=words)

    q.enqueue(make_and_send, ms.filename, words.filename, email)
    
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