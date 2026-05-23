from groq import Groq
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

THEME_KEYWORDS = [
    "advertising brand history",
    "business marketing strategy",
    "brand communication modern",
    "artificial intelligence technology",
    "storytelling communication",
    "consumer psychology behavior",
    "personal branding linkedin",
    "marketing mistake business",
    "data creativity analytics",
    "digital future communication",
]


def generate_post(theme):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )
    return response.choices[0].message.content.strip()


def get_unsplash_photo(keyword):
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        return None

    query = urllib.parse.quote(keyword)
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=1&orientation=landscape&client_id={access_key}"

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept-Version", "v1")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            if data["results"]:
                photo_url = data["results"][0]["urls"]["regular"]
                with urllib.request.urlopen(photo_url) as photo_response:
                    return photo_response.read()
    except Exception as e:
        print(f"Unsplash non disponibile: {e}")
    return None


def upload_image_to_linkedin(image_data, access_token, author_urn):
    # Step 1: registra l'upload
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    register_payload = json.dumps({
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }).encode()

    req = urllib.request.Request(register_url, data=register_payload, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")

    with urllib.request.urlopen(req) as response:
        register_data = json.loads(response.read())

    upload_url = register_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = register_data["value"]["asset"]

    # Step 2: carica l'immagine
    upload_req = urllib.request.Request(upload_url, data=image_data, method="PUT")
    upload_req.add_header("Authorization", f"Bearer {access_token}")
    upload_req.add_header("Content-Type", "image/jpeg")

    try:
        with urllib.request.urlopen(upload_req) as response:
            pass
    except urllib.error.HTTPError as e:
        if e.code != 201:
            raise

    return asset_urn


def post_to_linkedin(text, access_token, author_urn, asset_urn=None):
    url = "https://api.linkedin.com/v2/ugcPosts"

    content = {
        "shareCommentary": {"text": text},
        "shareMediaCategory": "IMAGE" if asset_urn else "NONE"
    }
    if asset_urn:
        content["media"] = [{
            "status": "READY",
            "description": {"text": ""},
            "media": asset_urn,
            "title": {"text": ""}
        }]

    payload = json.dumps({
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": content
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
    return THEMES[day % len(THEMES)], THEME_KEYWORDS[day % len(THEME_KEYWORDS)]


if __name__ == "__main__":
    theme, keyword = get_todays_theme()
    print(f"Tema: {theme[:60]}...")

    post_text = generate_post(theme)
    print(f"\nPost generato:\n{post_text}\n")

    access_token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    author_urn = os.environ["LINKEDIN_AUTHOR_URN"]

    # Cerca foto su Unsplash
    asset_urn = None
    print(f"Cerco foto per: {keyword}")
    image_data = get_unsplash_photo(keyword)
    if image_data:
        print("Foto trovata, carico su LinkedIn...")
        try:
            asset_urn = upload_image_to_linkedin(image_data, access_token, author_urn)
            print("Foto caricata!")
        except Exception as e:
            print(f"Errore caricamento foto: {e} — pubblico senza immagine")
    else:
        print("Nessuna foto trovata — pubblico senza immagine")

    status, response = post_to_linkedin(post_text, access_token, author_urn, asset_urn)

    if status == 201:
        print("Pubblicato su LinkedIn" + (" con foto!" if asset_urn else " (solo testo)"))
    else:
        print(f"Errore {status}: {response.decode()}")
        exit(1)
