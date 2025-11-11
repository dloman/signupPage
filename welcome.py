import smtplib
import logging
from email.mime.text import MIMEText
from jinja2 import Template 
import os, sys
from datetime import datetime
import requests


welcome_email = """
<!doctype html>
<html lang="en">

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Membership Page</title>

  <!-- Bootstrap core CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"
    integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">

  <style>
    .bd-placeholder-img {
      font-size: 1.125rem;
      text-anchor: middle;
      -webkit-user-select: none;
      -moz-user-select: none;
      user-select: none;
    }

    @media (min-width: 768px) {
      .bd-placeholder-img-lg {
        font-size: 3.5rem;
      }
    }
  </style>

</head>

<body>

  <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
    <symbol id="check" viewBox="0 0 16 16">
      <title>Check</title>
      <path
        d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z" />
    </symbol>
  </svg>

  <div class="container py-3">
    <header>
      <link rel="shortcut icon" href="https://signup.sbhackerspace.com/favicon.ico">
      <div class="d-flex flex-column flex-md-row align-items-center pb-3 mb-4 border-bottom">
        <a href="https://auth.sbhackerspace.com" class="d-flex align-items-center text-dark text-decoration-none">
          <img class="d-block mx-auto mb-9" src="https://store.sbhackerspace.com/static/logo.png" crossorigin=anonymous>

          <span class="fs-4"> Welcome To SBHX! </span>
        </a>
      </div>

      <div class="pricing-header p-3 pb-md-4 mx-auto text-center border-secondary">
        <h1 class="display-4 fw-normal">Welcome to SBHX!!!</h1>
      </div>
    </header>

<img alt="Santa Barbara Hackerspace, Inc." src="https://sbhackerspace.com/assets/images/carousel/sem_inside.jpg" style="margin-left: auto; margin-right: auto;" />

<h3>Hi {{ name }}! Welcome to The Santa Barbara Hackerspace!</h3>

<p>We're sure glad to have you aboard!  <a href="https://docs.google.com/document/d/1aj8J724yfNTiCDUZBPep998vWWXI7el3N5yYBvZt0zo/edit?usp=sharing" target="_blank">Some general housekeeping rules can be found here</a>.  Please take a moment and read through them before beginning a project at The Hackerspace.</p>


<p>The easiest way to get in contact with a Hackerspace board member, or any of our other members, <a href="https://join.slack.com/t/sbhackerspace/shared_invite/enQtMzgwMzcxNTM3MjM4LTQ5ZWU3OTllMDhmZjY4NjJhMWUzMWQyYTIzYmU0NWEzOWJhZmJhMjFjMTQxNGE1OTY1NDFmM2I3YzdmNTQ1NDM" target="_blank">is in our slack channel</a> </p>

<p>We are a federally recognized 501(c)(3) organization!  If you would like to make a donation, either monetary or equipment, please let us know!  We continue to exist completely as a result of donations and support from people like you!  We will provide you with a donation receipt which has our Tax ID number, and you can deduct the value of your donation on your taxes! (Unfortunately, your membership fee is not deductible.)  We do ask that you please talk to us before planning to donate equipment or material, because sometimes we just can't use whatever it might be that you're thinking about donating.  We appreciate the thought, but all too often that sort of thing just leads to clutter, and we want to try to avoid that as much as possible!</p>

<p>So that's it!  You're now officially a member of The Santa Barbara Hackerspace, Inc.  There is still a bit of housekeeping though, namely, getting you set up with your very own ID card to access The Space!  The best time to take care of that is on a Saturday afternoon/evening (that's when most of the board members will be present anyway), but if you'd like to take care of it sooner, or Saturdays aren't good for you, please feel free to reach out on Slack or email to set up an appointment for someone to help you with that sooner.  It's not a bother, we promise!  And if you find that you're leaving, and you're the last person in The Space, please make sure to turn off all the lights, and lock all the doors (roll-up doors included).  The roll-up doors can be locked by sliding the locking rails into place (there are two on the side door, at the very bottom of the door, and one on the back door, about waist height on the right-hand side).  The main back door is locked by pressing the padlock button (the very center button) on the keypad.  Sometimes it doesn't lock all the way, so listen for the sound of the deadbolt moving to make sure it's really locked.  The lights are controlled by the big plastic buttons on the walls, or they can also be controlled from a web page we've set up (note that the help page is only accessible internally): <a href="http://help/">http://help/</a> (except for the shop lights, those are all using normal light switches on the back wall next to the door).</p>

<p>Here are all the links again, in case they didn't work right in the body of the email, you can just copy them from here and paste them into your browser:</p>
<p>SBHX General Guidelines/Rules: <a href="https://docs.google.com/document/d/1aj8J724yfNTiCDUZBPep998vWWXI7el3N5yYBvZt0zo/edit?usp=sharing">https://docs.google.com/document/d/1aj8J724yfNTiCDUZBPep998vWWXI7el3N5yYBvZt0zo/edit?usp=sharing</a></p>
<p>Join us on Slack!: <a href="https://join.slack.com/t/sbhackerspace/shared_invite/enQtMzgwMzcxNTM3MjM4LTQ5ZWU3OTllMDhmZjY4NjJhMWUzMWQyYTIzYmU0NWEzOWJhZmJhMjFjMTQxNGE1OTY1NDFmM2I3YzdmNTQ1NDM" target="_blank">https://join.slack.com/t/sbhackerspace/shared_invite/enQtMzgwMzcxNTM3MjM4LTQ5ZWU3OTllMDhmZjY4NjJhMWUzMWQyYTIzYmU0NWEzOWJhZmJhMjFjMTQxNGE1OTY1NDFmM2I3YzdmNTQ1NDM</a></p>
<p>The Help Page (Lots of good information, and control the lights/projector): <a href="http://help/">http://help/</a></p>

<p>We hope to see you soon!</p>

<p>-The Santa Barbara Hackerspace Board of Directors</p>
<br />
<p>P.S.:  One more thing to mention.  Although it almost never happens, occasionally we do have people come in who mistreat our equipment.  Since we can't be present all the time to watch everyone and make sure everyone is behaving, we've set up cameras in all of the main common rooms.  This is for our safety as well as yours, and for accountability in the rare case when we discover something missing, broken, or handled irresponsibly.  So smile!  You're on camera!</p>
</body>
</html>
"""
template = Template(welcome_email)

def send_welcome_email(name, email, logger):
    html_message = MIMEText(template.render(name=name), 'html')
    html_message['Subject'] = "Welcome to SBHX!"
    html_message['From'] = 'admin@sbhackerspace.com'
    html_message['To'] = 'SBHX_Welcome@sbhackerspace.com'
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login('auth@sbhackerspace.com', os.environ['GMAIL_APP_PASSWORD'])
       smtp_server.sendmail('auth@sbhackerspace.com', email, html_message.as_string())
    logger.info(f"Welcome Message sent {name} {email}")

def get_groups(groups):
    authentik_groups = []
    for group in groups:
        group = group.lower()
        if "basic" in group:
            authentik_groups.append('basic-member')
        if "student" in group:
            authentik_groups.append('student-member')
        if "advanced" in group:
            authentik_groups.append('advanced-member')
    return authentik_groups

def on_signup(name, email, subscription_id, groups, logger):
    key = "iuu5Ati7vaiG5ahyone3aeSespohsho7Aahxoh6GoxaeB6XiezooVaiN3baxahF7A"
    username = name.lower().replace(' ', '')
    logger.info(f"username = {username}")
    response = requests.post("http://10.18.14.203:8000/create_user", json={
        'email': email,
        'name': name,
        'username': username,
        'groups': get_groups(groups),
        'timestamp': datetime.now().isoformat(),
        'attributes': { "card_id": [], 'member_since': datetime.now().isoformat(), 'subscription_id': [subscription_id]},
        'shared_secret':key})

    logger.info(f"response = {response}")
    send_welcome_email(name, email, logger)

if __name__ == "__main__":

    logging.basicConfig(level=DEFAULT_LOG_LEVEL, format=DEFAULT_LOG_FORMAT)
    # Get a logger instance for your module
    logger = logging.getLogger(__name__)

    if len(sys.argv) > 2:
        on_signup(name =sys.argv[1], email=sys.argv[2], subscription_id='fffff', groups=["student"], logger = logger)
    else:
        print("usage: python3 welcome.py NAME EMAIL")
