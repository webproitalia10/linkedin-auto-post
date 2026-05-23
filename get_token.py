"""
Esegui questo script UNA VOLTA per ottenere il token LinkedIn.
Poi salva i valori come GitHub Secrets.

Uso:
    LINKEDIN_CLIENT_SECRET=xxx python3 get_token.py
"""

import urllib.parse
import urllib.request
import json
import webbrowser
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID = "77d5z8eyynud8s"
REDIRECT_URI = "http://localhost:8080"
SCOPES = "openid profile w_member_social"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        print(f"\nRisposta LinkedIn ricevuta: {self.path}")
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family:sans-serif;text-align:center;padding:50px">
                <h1>Autorizzazione completata!</h1>
                <p>Puoi chiudere questa finestra e tornare al terminale.</p>
                </body></html>
            """)
        elif "error" in params:
            error = params.get("error", ["?"])[0]
            desc = params.get("error_description", ["nessun dettaglio"])[0]
            print(f"Errore OAuth: {error} — {desc}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Errore: {error}</h1><p>{desc}</p></body></html>".encode())
        else:
            print(f"Parametri ricevuti: {params}")
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def get_access_token(code, client_secret):
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": client_secret,
    }).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        print(f"Errore {e.code}: {e.read().decode()}")
        raise


def get_person_urn(access_token):
    req = urllib.request.Request("https://api.linkedin.com/v2/userinfo")
    req.add_header("Authorization", f"Bearer {access_token}")

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
        return data.get("sub")


def main():
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
    if not client_secret:
        print("Errore: esegui con LINKEDIN_CLIENT_SECRET=xxx python3 get_token.py")
        return

    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 120
    print("Server pronto su localhost:8080")
    print("Apertura browser per autorizzare l'app LinkedIn...")
    webbrowser.open(auth_url)
    print("In attesa di autorizzazione (autorizza nel browser)...")

    while not auth_code:
        server.handle_request()
        if not auth_code:
            print("Richiesta ricevuta senza codice, continuo ad aspettare...")

    if not auth_code:
        print("Errore: autorizzazione non completata.")
        return

    print("Codice ricevuto, ottengo il token...")
    token_data = get_access_token(auth_code, client_secret)
    access_token = token_data["access_token"]

    person_sub = get_person_urn(access_token)
    author_urn = f"urn:li:person:{person_sub}"

    print("\n" + "=" * 55)
    print("SALVA QUESTI VALORI COME GITHUB SECRETS:")
    print("=" * 55)
    print(f"\nLINKEDIN_ACCESS_TOKEN\n{access_token}\n")
    print(f"LINKEDIN_AUTHOR_URN\n{author_urn}\n")
    print("=" * 55)
    print("\nIl token dura 2 mesi. Dopo, riesegui questo script.")


if __name__ == "__main__":
    main()
