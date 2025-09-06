import flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import request
import braintree
import datetime
import os
import json
from dotenv import load_dotenv
import logging
import uuid
import hmac
import hashlib

load_dotenv()

app = flask.Flask(__name__)
app.logger = logging.getLogger('waitress')
app.logger.setLevel(logging.INFO)
total_donated = 0.0
try:
    with open('donationTotal.json', 'r') as openfile:
        total_donated = float(json.load(openfile)["total_donated"])
except:
    app.logger.error("An exception occurred reading total donated")
    total_donated = 2000

def get_enviroment(env):
    if env == "Production":
        return braintree.Environment.Production
    return braintree.Environment.Sandbox

def get_plan_id(membership_type):
    if membership_type == "student": # $50/month
        return "45kw"
    elif membership_type == "basic": # $75/month
        return "sjxm"
    elif membership_type == "yearly_basic":# $900/year
        return "hbfj"
    elif membership_type == "yearly_advanced": # $1200/year
        return "m27j"
    elif membership_type == "yearly_student": # $600/year
        return "63v8"
    elif membership_type == "old_advanced": # $100/month
        return "bq82"
    elif membership_type == "very_old_basic": # $30/month
        return "4r2w"
    elif membership_type == "fume_hood": # $200/month
        return "ssgr"
    elif membership_type == "paypal_basic": # $45/month
        return "754y"
    elif membership_type == "old_basic": # $50/month
        return "jpf6"
    return "j3y6" # advanced $125/month

def generate_hash(hash_uuid = None, hash_date = None):
    if hash_uuid is None:
        has_uuid = uuid.uuid4()

    if hash_date is None:
        hash_date = datetime.date.today()
    secret_key = b"secret key to prevent fraud"
    message = f"{hash_uuid}{hash_date.isoformat()}"
    message = message.encode('utf-8')

    # Create an HMAC object using SHA-256 as the digestmod
    # The key and message should be byte strings
    hmac_obj = hmac.new(secret_key, message, hashlib.sha256)
    # Get the hexadecimal representation of the HMAC digest
    return f"{hmac_obj.hexdigest()}"

bt_gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=get_enviroment(os.environ["ENVIRONMENT"]),
        merchant_id=os.environ["MERCHANT_ID"],
        public_key=os.environ["PUBLIC_KEY"],
        private_key=os.environ["PRIVATE_KEY"],
    ))

@app.route('/')
def index():
    global total_donated
    return flask.render_template(
              'donate.html',
              total_donated="{:,}".format(int(total_donated)),
              percent="{:}".format(int(100*total_donated/100000.)),
              year = datetime.date.today().year)


@app.route('/donation_storefront')
def donate_store():
    global total_donated
    return flask.render_template(
              'donation_store.html',
              year = datetime.date.today().year)

@app.route('/update_info')
def update_info():
    membership_type = request.args.get('membership_type')
    amount = request.args.get('price')
    return flask.render_template(
            'update.html',
            membership_type=membership_type,
            price=amount,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)


@app.route('/update', methods=['POST'])
def update():
    collection = bt_gateway.customer.search(braintree.CustomerSearch.email == request.form.get("email"))

    app.logger.info(f'updating {request.form.get("first_name")} {request.form.get("last_name")} ')
    for customer in collection.items:
        app.logger.info(f"updating cusomter {customer}")
        result = bt_gateway.customer.update(
            customer.id,
            {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name"),
                "email": request.form.get("email"),
                "credit_card": {
                    "options": { "make_default": True, "verify_card": True },
                    "billing_address": {
                        "first_name": request.form.get("first_name"),
                        "last_name": request.form.get("last_name"),
                        "street_address": request.form.get("address"),
                        "extended_address": request.form.get("address2"),
                        "locality": request.form.get("city"),
                        "region": request.form.get("state"),
                        "postal_code": request.form.get("zip_code"),
                    },
                },
                "payment_method_nonce": request.form.get("payment_method_nonce"),
            })
        app.logger.debug(f"result = {result}")
        if not result.is_success:
            app.logger.error(f"ERROR: {result.message}")
            return flask.render_template('error.html')

        if len(result.customer.payment_methods) < 1:
            app.logger.error("ERROR: no payment methods ")
            return flask.render_template('error.html')

        for card in result.customer.payment_methods:
            sub_result = bt_gateway.subscription.create({
                "payment_method_token": card.token,
                "plan_id": get_plan_id(request.form.get("membership_type")),
                })
            if sub_result.is_success:
                return flask.render_template(
                        'thanks.html',
                        title="Membership Information Updated",
                        thanks="Thank you for continuing to be a sustaining sbhx member.")

            app.logger.error(f"ERROR: {sub_result.errors}")
    app.logger.error(f"ERROR: unable to find customers")
    return flask.render_template('error.html')


@app.route('/donate', methods=['POST'])
def donate():
    app.logger.info(f'trying to buy {request.form.get("item")} ${request.form.get("amount")}')
    request_uuid = uuid.uuid4()
    return flask.render_template(
            'form_donate.html',
            title=request.form.get("title"),
            price=request.form.get("amount"),
            item=request.form.get("item"),
            client_token_from_server= bt_gateway.client_token.generate(),
            request_uuid=request_uuid,
            request_hash=generate_hash(request_uuid),
            request_date=datetime.date.today(),
            year=datetime.date.today().year)

@app.route('/basic')
def basic():
    return flask.render_template(
            'form.html',
            membership_type="basic",
            price=75,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/student')
def student():
    return flask.render_template(
            'form.html',
            membership_type="student",
            price=50,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/advanced')
def advanced():
    return flask.render_template(
            'form.html',
            membership_type="advanced",
            price=125,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/yearly_advanced')
def yearly_advanced():
    return flask.render_template(
            'form.html',
            membership_type="yearly_advanced",
            price=1200,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/yearly_basic')
def yearly_basic():
    return flask.render_template(
            'form.html',
            membership_type="yearly_basic",
            price=900,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/yearly_student')
def yearly_student():
    return flask.render_template(
            'form.html',
            membership_type="yearly_student",
            price=600,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/membership_info')
def membership_info():
    global total_donated
    return flask.render_template(
              'index.html',
              year = datetime.date.today().year)

@app.route("/signup", methods=['POST'])
def signup():
    if len(list(bt_gateway.customer.search(braintree.CustomerSearch.email == request.form.get("email")).items)) > 0:
        print("found customer redirecting to update endpoint")
        return flask.redirect(flask.url_for('update'), code=307)

    result = bt_gateway.customer.create({
        "first_name": request.form.get("first_name"),
        "last_name": request.form.get("last_name"),
        "email": request.form.get("email"),
        "credit_card": {
            "options": { "verify_card": True },
            "billing_address": {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name"),
                "street_address": request.form.get("address"),
                "extended_address": request.form.get("address2"),
                "locality": request.form.get("city"),
                "region": request.form.get("state"),
                "postal_code": request.form.get("zip_code"),
            },
        },
        "payment_method_nonce": request.form.get("payment_method_nonce"),
        })
    if not result.is_success:
        app.logger.error(f"ERROR: {result.errors}")
        return flask.render_template('error.html')

    if len(result.customer.payment_methods) < 1:
        app.logger.error("ERROR: no payment methods ")
        return flask.render_template('error.html')

    for card in result.customer.payment_methods:
        sub_result = bt_gateway.subscription.create({
            "payment_method_token": card.token,
            "plan_id": get_plan_id(request.form.get("membership_type")),
            })
        if sub_result.is_success:
            return flask.render_template(
                    'thanks.html',
                    title="Membership Information Updated",
                    thanks="Thank you for becoming a sustaining SBHX Member")

        app.logger.error(f"ERROR: {sub_result.errors}")
    return flask.render_template('error.html')

@app.route("/donation_transaction", methods=['POST'])
def donation_transaction():
    app.logger.info(f'{request.form.get("first_name")} {request.form.get("last_name")} is trying to buy {request.form.get("item")} ${request.form.get("amount")} {request.form.get("email")} anon = ${request.form.get("anonymous")} {request.environ.get("HTTP_X_REAL_IP", request.remote_addr)}')
    global total_donated

    # check that hash in the request comes from app and is recent
    request_date = datetime.date.fromisoformat(request.form.get("date"))
    if (datetime.date.today() - request_date).days > 2:
        app.logger.error(f"ERROR: {request_date.isoformat()} is to far away from today {datetime.date.today()}")
        return flask.render_template('error.html')

    generated_hash = generate_hash(request.form.get("uuid"), request_date)
    if request.form.get("hash") != generated_hash:
        app.logger.error(f"ERROR: {request_date.isoformat()} {request.form.get('hash')} generated hash = {generated_hash}")
        return flask.render_template('error.html')

    app.logger.info(f"before total amount donated = {total_donated}")
    result = bt_gateway.transaction.sale({
        "amount": request.form.get("amount"),
        "payment_method_nonce": request.form.get("payment_method_nonce"),
        "device_data": request.form.get("device_data"),
        "options": { "submit_for_settlement": True },
        'customer': {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name"),
                "email": request.form.get("email")
                },
        'billing': {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name"),
                "street_address": request.form.get("address"),
                "extended_address": request.form.get("address2"),
                "locality": request.form.get("city"),
                "region": request.form.get("state"),
                "postal_code": request.form.get("zip_code"),
            },
        })
    if result.is_success:
        total_donated += float(request.form.get("amount"))
        app.logger.info(f"after total amount donated = {total_donated}")
        with open("donationTotal.json", 'w') as f:
            json.dump({"total_donated": total_donated}, f)
        return flask.render_template(
                'thanks.html',
                title="Donation Complete!",
                thanks="Thank you for being a sustaining SBHX Donor")

    app.logger.error(f"ERROR: {result} {result.errors}")
    return flask.render_template('error.html')

if __name__ == "__main__":
    app.static_folder = 'static'
    app.send_static_file('static/favicon.ico')
    app.send_static_file('static/logo.png')
    app.send_static_file('js/form-validation.js')
    app.send_static_file('css/form-validation.css')
    app.send_static_file('js/form.js')
    app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
            )
    app.config["TEMPLATES_AUTO_RELOAD"] = True
