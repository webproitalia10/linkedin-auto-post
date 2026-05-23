from google import genai
import urllib.request
import urllib.parse
import json
import os
from datetime import datetime

THEMES = [
    "caso storico famoso di marketing (scegli tra: Nike Just Do It, Apple 1984, Dove Real Beauty, Volkswagen Think Small, Red Bull Stratos, Old Spice, Airbnb, o altri casi celebri). Racconta la storia in modo coinvolgente con dati reali.",
    "importanza strategica del marketing per il successo di un'azienda o professionista. Usa un esempio concreto.",
    "come i brand stanno comunicando su temi contemporanei (sostenibilità, inclusione, AI, o altro tema attuale). Prendi una posizione chiara.",
    "intelligenza artificiale e il suo impatto concreto sul marketing e la comunicazione oggi.",
    "storytelling: una tecnica o principio specifico per comunicare in modo più efficace, con esempio pratico.",
    "psicologia del consumatore: un bias cognitivo o leva emotiva specifica e come influenza le decisioni d'acquisto.",
    "personal branding: un consiglio concreto e non ovvio per costruire autorevolezza su LinkedIn.",
    "un errore comune e costoso nel marketing o nella comunicazione, con la soluzione.",
    "come bilanciare dati e creatività nelle decisioni di marketing. Usa un caso reale.",
    "il futuro della comunicazione digitale: una tendenza concreta che cambierà il settore nei prossimi 2 anni.",
]


def generate_post(theme):
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = f"""Sei un esperto di marketing e comunicazione con 15 anni di esperienza che pubblica contenuti su LinkedIn.

Scrivi un post LinkedIn sul tema: {theme}

Regole OBBLIGATORIE:
- Prima riga: hook che ferma lo scroll (massimo 8 parole, crea curiosità o stupore, può essere una statistica sorprendente o un'affermazione controcorrente)
- Scritto in italiano
- Molti a capo (ogni 1-2 frasi)
- Tono diretto e autorevole, mai accademico o generico
- Nessuna emoji
- Chiudi con una domanda che inviti al commento
- 3-4 hashtag rilevanti alla fine
- Lunghezza: 150-250 parole

Scrivi SOLO il testo del post."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()


def post_to_linkedin(text, access_token, author_urn):
    url = "https://api.linkedin.com/v2/ugcPosts"

    payload = json.dumps({
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")

    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get_todays_theme():
    day = datetime.now().timetuple().tm_yday
    return THEMES[day % len(THEMES)]


if __name__ == "__main__":
    theme = get_todays_theme()
    print(f"Tema: {theme[:60]}...")

    post_text = generate_post(theme)
    print(f"\nPost generato:\n{post_text}\n")

    access_token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    author_urn = os.environ["LINKEDIN_AUTHOR_URN"]

    status, response = post_to_linkedin(post_text, access_token, author_urn)

    if status == 201:
        print("Pubblicato su LinkedIn!")
    else:
        print(f"Errore {status}: {response.decode()}")
        exit(1)
