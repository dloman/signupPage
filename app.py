import flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import request
import braintree
import datetime
import os
import json
from dotenv import load_dotenv
import logging

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
    if membership_type == "student":
        return "45kw"
    elif membership_type == "Basic":
        return "sjxm"
    return "j3y6"

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
        app.logger.debug(f"result = {result}")
        if not result.is_success:
            app.logger.error(f"ERROR: {result.message}")
            return flask.render_template('error.html')
        return flask.render_template(
                'thanks.html',
                title="Membership Information Updated",
                thanks="Thank you for continuing to be a sustaining sbhx member.")
    app.logger.error(f"ERROR: unable to find customers")
    return flask.render_template('error.html')


@app.route('/donate', methods=['POST'])
def donate():
    app.logger.info(f'trying to buy {request.form.get("item")} ${request.form.get("amount")}')
    return flask.render_template(
            'form_donate.html',
            title=request.form.get("title"),
            price=request.form.get("amount"),
            item=request.form.get("item"),
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/basic')
def basic():
    return flask.render_template(
            'form.html',
            membership_type="Basic",
            price=75,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/advanced')
def advanced():
    return flask.render_template(
            'form.html',
            membership_type="Advanced",
            price=125,
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route("/signup", methods=['POST'])
def signup():
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

    if len(result.customer.credit_cards) < 1:
        app.logger.error("ERROR: no credit cards ")
        return flask.render_template('error.html')

    for card in result.customer.credit_cards:
        sub_result = bt_gateway.subscription.create({
            "payment_method_token": card.token,
            "plan_id": get_plan_id(request.form.get("plan_id")),
            "options": {
                "submit_for_settlement": True
                }
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
    app.logger.info(f'{request.form.get("first_name")} {request.form.get("last_name")} is trying to buy {request.form.get("item")} ${request.form.get("amount")}')
    global total_donated
    app.logger.info(f"before total amount donated = {total_donated}")
    result = bt_gateway.transaction.sale({
        "amount": request.form.get("amount"),
        "payment_method_nonce": request.form.get("payment_method_nonce"),
        "device_data": request.form.get("device_data"),
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
                title="Donatation Complete!",
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
