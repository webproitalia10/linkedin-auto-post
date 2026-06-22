from groq import Groq
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import json
import os
import random
import re
from datetime import datetime

RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.corriere.it/rss/economia.xml",
    "https://www.ilsole24ore.com/rss/economia--finanza.xml",
    "https://feeds.feedburner.com/fastcompany/headlines",
    "https://www.wired.com/feed/rss",
]

FALLBACK_THEMES = [
    "come i brand stanno comunicando su temi contemporanei. Prendi una posizione chiara.",
    "intelligenza artificiale e il suo impatto concreto sul marketing e la comunicazione oggi.",
    "storytelling: una tecnica specifica per comunicare in modo più efficace, con esempio pratico.",
    "psicologia del consumatore: un bias cognitivo specifico e come influenza le decisioni d'acquisto.",
    "personal branding: un consiglio concreto per costruire autorevolezza su LinkedIn.",
]


def get_todays_news():
    feeds = RSS_FEEDS.copy()
    random.shuffle(feeds)

    for feed_url in feeds:
        try:
            req = urllib.request.Request(feed_url)
            req.add_header("User-Agent", "Mozilla/5.0")
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()

            root = ET.fromstring(content)
            items = root.findall(".//item")

            if items:
                item = random.choice(items[:8])
                title = item.findtext("title", "").strip()
                description = item.findtext("description", "").strip()
                description = re.sub(r"<[^>]+>", "", description)[:600]
                if title:
                    print(f"Notizia trovata: {title[:80]}")
                    return title, description
        except Exception as e:
            print(f"Feed non disponibile ({feed_url[:40]}...): {e}")
            continue

    return None, None


def generate_post_from_news(title, description):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    prompt = f"""Sei un professionista di marketing e comunicazione con una voce diretta e scomoda su LinkedIn. Non sei un professore, sei un praticante.

La notizia di oggi è:
TITOLO: {title}
DETTAGLIO: {description}

Scrivi un post LinkedIn breve e provocatorio che parte da questa notizia.

Regole OBBLIGATORIE:
- PRIMA RIGA (il gancio): è la cosa più importante del post. Deve fermare lo scroll. Massimo 6 parole. Deve essere un'affermazione secca, scomoda, controcorrente o sorprendente. NON una domanda. Esempi di hook forti: "Il tuo brand parla. Nessuno ascolta.", "La trasparenza non paga. Paga la storia.", "Il 90% dei lanci fallisce per questo."
- Seconda riga: lasciala vuota (a capo)
- Poi sviluppa il post in modo diretto e umano — come se stessi parlando a un collega davanti a un caffè
- Prendi una posizione netta, anche impopolare — il post deve generare reazioni e commenti
- VIETATO usare: "secondo gli studi", "la ricerca dimostra", "è fondamentale", "in conclusione", "è essenziale che", "risulta evidente"
- Se citi un dato, integralo nel discorso in modo naturale, non da report
- Molti a capo (ogni 1-2 frasi)
- Nessuna emoji
- NO domande finali — chiudi con una provocazione o un'affermazione forte che fa pensare
- 6-8 hashtag rilevanti (mix marketing, comunicazione, attualità, settore)
- Lunghezza: 120-170 parole (corto e incisivo, non di più)

Scrivi SOLO il testo del post."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()


def generate_post_fallback():
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    theme = random.choice(FALLBACK_THEMES)

    prompt = f"""Sei un professionista di marketing e comunicazione con una voce diretta e scomoda su LinkedIn. Non sei un professore, sei un praticante.

Scrivi un post LinkedIn breve e provocatorio sul tema: {theme}

Regole OBBLIGATORIE:
- PRIMA RIGA (il gancio): è la cosa più importante del post. Deve fermare lo scroll. Massimo 6 parole. Deve essere un'affermazione secca, scomoda, controcorrente o sorprendente. NON una domanda. Esempi di hook forti: "Il tuo brand parla. Nessuno ascolta.", "La trasparenza non paga. Paga la storia.", "Il 90% dei lanci fallisce per questo."
- Seconda riga: lasciala vuota (a capo)
- Poi sviluppa il post in modo diretto e umano — come se stessi parlando a un collega davanti a un caffè
- Prendi una posizione netta, anche impopolare — il post deve generare reazioni e commenti
- VIETATO usare: "secondo gli studi", "la ricerca dimostra", "è fondamentale", "in conclusione", "è essenziale che", "risulta evidente"
- Se citi un dato, integralo nel discorso in modo naturale, non da report
- Molti a capo
- Nessuna emoji
- NO domande finali — chiudi con una provocazione o un'affermazione forte che fa pensare
- 6-8 hashtag rilevanti (mix marketing, comunicazione, attualità, settore)
- Lunghezza: 120-170 parole (corto e incisivo, non di più)

Scrivi SOLO il testo del post."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()


def extract_image_keyword(title):
    stopwords = {"il","la","lo","le","gli","i","un","una","di","da","in","con","su","per","tra","fra","che","e","è","a","al","del","della","delle","dei","degli","nel","nella"}
    words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
    keywords = [w for w in words if w not in stopwords]
    return " ".join(keywords[:3]) if keywords else "business news"


def get_unsplash_photo(keyword):
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        return None

    query = urllib.parse.quote(keyword)
    page = random.randint(1, 5)
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=10&page={page}&orientation=landscape&client_id={access_key}"

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept-Version", "v1")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            if data["results"]:
                photo = random.choice(data["results"])
                photo_url = photo["urls"]["regular"]
                with urllib.request.urlopen(photo_url) as photo_response:
                    return photo_response.read()
    except Exception as e:
        print(f"Unsplash non disponibile: {e}")
    return None


def upload_image_to_linkedin(image_data, access_token, author_urn):
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


if __name__ == "__main__":
    access_token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    author_urn = os.environ["LINKEDIN_AUTHOR_URN"]

    # Cerca notizia del giorno
    title, description = get_todays_news()

    if title:
        post_text = generate_post_from_news(title, description)
        keyword = extract_image_keyword(title)
    else:
        print("Nessuna notizia trovata — uso tema di fallback")
        post_text = generate_post_fallback()
        keyword = "business marketing"

    print(f"\nPost generato:\n{post_text}\n")

    # Foto Unsplash
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
