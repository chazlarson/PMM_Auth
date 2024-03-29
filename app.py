from flask import Flask, render_template, request
import requests
import secrets
import re

app = Flask(__name__)

class PostDetails:
    def __init__(self, tab, trakt_client_id, trakt_client_secret, trakt_pin, code_verifier, mal_client_id, mal_client_secret, mal_local_url):
        self.tab = tab
        self.trakt_client_id = trakt_client_id
        self.trakt_client_secret = trakt_client_secret
        self.trakt_pin = trakt_pin
        self.code_verifier = code_verifier
        self.mal_client_id = mal_client_id
        self.mal_client_secret = mal_client_secret
        self.mal_local_url = mal_local_url

def validate(post_details):
    if post_details.tab == "trakt":
        return validate_trakt(post_details.trakt_client_id, post_details.trakt_client_secret, post_details.trakt_pin)
    else:
        return validate_mal(post_details.code_verifier, post_details.mal_client_id, post_details.mal_client_secret, post_details.mal_local_url)
    
def validate_trakt(client_id, client_secret, pin):
    redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    base_url = "https://api.trakt.tv"

    results = ""

    json = {
        "code": pin,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    response = requests.post(f"{base_url}/oauth/token", json=json, headers={"Content-Type": "application/json"})

    if response.status_code != 200:
        results = "Trakt Error: Invalid trakt pin. If you're sure you typed it in correctly your client_id or client_secret may be invalid"
    else:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {response.json()['access_token']}",
            "trakt-api-version": "2",
            "trakt-api-key": client_id,
        }
    
        validation_response = requests.get(f"{base_url}/users/settings", headers=headers)

        if validation_response.status_code == 423:
            results = "Trakt Error: Account is locked; please contact Trakt Support"
        else:
            results = f"########## GENERATED BY TRAKTAUTH ##########\ntrakt:\n  client_id: {client_id}\n  client_secret: {client_secret}\n  authorization:\n    access_token: {response.json()['access_token']}\n    token_type: {response.json()['token_type']}\n    expires_in: {response.json()['expires_in']}\n    refresh_token: {response.json()['refresh_token']}\n    scope: {response.json()['scope']}\n    created_at: {response.json()['created_at']}\n  pin:\n############################################\n"

    return results

def validate_mal(code_verifier, client_id, client_secret, localhost_url):
    results = ""

    match = re.search("code=([^&]+)", str(localhost_url))

    if not match:
        results = "Couldn't find the required code in that URL."
    else:
        code = match.group(1)

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
        }

        session = requests.Session()
        new_authorization = session.post("https://myanimelist.net/v1/oauth2/token", data=data).json()

        if "error" in new_authorization:
            results = "ERROR: invalid code."
        else:
            results = f"########## GENERATED BY MALAUTH ##########\nmal:\n  client_id: {client_id}\n  client_secret: {client_secret}\n  authorization:\n    access_token: {new_authorization['access_token']}\n    token_type: {new_authorization['token_type']}\n    expires_in: {new_authorization['expires_in']}\n    refresh_token: {new_authorization['refresh_token']}\n  localhost_url: {localhost_url}\n  cache_expiration: 60\n############################################\n"

    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    if request.method == 'POST':
        tab = request.form.get('tab')
        trakt_client_id = request.form.get('trakt_client_id')
        trakt_client_secret = request.form.get('trakt_client_secret')
        trakt_pin = request.form.get('trakt_pin')

        code_verifier = request.form.get('code_verifier')
        mal_client_id = request.form.get('mal_client_id')
        mal_client_secret = request.form.get('mal_client_secret')
        mal_local_url = request.form.get('mal_local_url')

        post_details = PostDetails(tab, trakt_client_id, trakt_client_secret, trakt_pin, code_verifier, mal_client_id, mal_client_secret, mal_local_url)

        result = validate(post_details)
    else:
        code_verifier = secrets.token_urlsafe(100)[:128]

    return render_template('index.html', result=result, code_verifier=code_verifier)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
