import flask
from flask import request
import braintree
import datetime
import os

app = flask.Flask(__name__)

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
    return flask.render_template('index.html', year = datetime.date.today().year)

@app.route('/update_info')
def update_info():
    return flask.render_template(
            'update.html',
            client_token_from_server= bt_gateway.client_token.generate(),
            year = datetime.date.today().year)

@app.route('/update', methods=['POST'])
def update():
    collection = bt_gateway.customer.search(braintree.CustomerSearch.email == request.form.get("email"))

    for customer in collection.items:
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
        if not result.is_success:
            print(f"ERROR: {result.errors}")
            return flask.render_template('error.html')
        return flask.render_template(
                'thanks.html',
                title="Membership Information Updated",
                thanks="Thank you for continuing to be a sustaining sbhx member.")
    print(f"ERROR: unable to find customers")
    return flask.render_template('error.html')

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
        print(f"ERROR: {result.errors}")
        return flask.render_template('error.html')

    if len(result.customer.credit_cards) < 1:
        print("ERROR: no credit cards ")
        return flask.render_template('error.html')

    for card in result.customer.credit_cards:
        sub_result = bt_gateway.subscription.create({
            "payment_method_token": card.token,
            "plan_id": get_plan_id(request.form.get("plan_id"))
            })
        if sub_result.is_success:
            return flask.render_template(
                    'thanks.html',
                    title="Membership Information Updated",
                    thanks="Thank you for becoming a sustaining SBHX Member")

        print(f"ERROR: {sub_result.errors}")
    return flask.render_template('error.html')

if __name__ == "__main__":
    #app.static_folder = 'static'
    app.send_static_file('favicon.ico')
    app.send_static_file('logo.png')
    app.send_static_file('js/form-validation.js')
    app.send_static_file('css/form-validation.css')
    app.send_static_file('js/form.js')
