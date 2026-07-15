import streamlit as st
import imaplib
import email
from email.header import decode_header
import datetime
import re

# Configuration de la page pour le mobile
st.set_page_config(
    page_title="Raffle Tracker Amazon",
    page_icon="🎉",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURATION (À MODIFIER ICI) ---
IMAP_SERVER = "imap.mail.me.com"
EMAIL_PRINCIPAL = "alexis.dupont2@icloud.com"  # <--- METS TON EMAIL ENTRE LES GUILLEMETS
PASSWORD = "btyd-sevh-vioq-hxca"  
# --------------------------------------

# Interface de l'application (plus de case email !)
st.title("🎉 Amazon Raffle Tracker")
st.write("Toutes vos victoires redirigées au même endroit.")

jours_arriere = st.slider("Nombre de jours à analyser :", min_value=1, max_value=30, value=1)
mot_cle = st.text_input("Mot-clé dans le sujet (ex: gagné, félicitations) :", value="gagné")

# Fonction de récupération des mails
def fetch_raffles(days, keyword):
    wins = []
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_PRINCIPAL, PASSWORD)
        mail.select("inbox")

        date_target = (datetime.date.today() - datetime.timedelta(days=days-1)).strftime("%d-%b-%Y")
        
        status, messages = mail.search(None, f'(SINCE "{date_target}" FROM "amazon")')
        
        if status != "OK":
            return False, "Erreur lors de la recherche des emails."

        email_ids = messages[0].split()
        
        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    if keyword.lower() not in subject.lower():
                        continue

                    email_date = msg["Date"]
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    break
                                except:
                                    pass
                    else:
                        body = msg.get_payload(decode=True).decode()

                    match = re.search(r"article\s*:\s*(.*)", body, re.IGNORECASE)
                    article_name = match.group(1).strip() if match else "Nom de l'article introuvable"
                    
                    wins.append({
                        "article": article_name,
                        "sujet": subject,
                        "date": email_date
                    })

        mail.logout()
        return True, wins
    except imaplib.IMAP4.error:
        return False, "Identifiants incorrects. Vérifiez l'email principal dans le code."
    except Exception as e:
        return False, f"Erreur de connexion : {str(e)}"

# Bouton d'action sur mobile
if st.button("🔄 Actualiser les victoires", use_container_width=True):
    with st.spinner("Analyse de la boîte principale en cours..."):
        success, result = fetch_raffles(jours_arriere, mot_cle)
        
        if success:
            if len(result) == 0:
                st.info("Aucune victoire trouvée pour cette période. Continuez d'y croire ! 💪")
            else:
                st.success(f"🎉 {len(result)} victoire(s) détectée(s) depuis tous vos alias !")
                for idx, win in enumerate(result, 1):
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #f9f9f9;">
                            <h4 style="margin: 0; color: #ff9900;">🎁 Victoire #{idx}</h4>
                            <p style="margin: 5px 0; font-weight: bold; font-size: 16px;">{win['article']}</p>
                            <small style="color: #666;">Objet : {win['sujet']}<br>Reçu le : {win['date']}</small>
                        </div>
                        """, unsafe_value=True)
        else:
            st.error(result)
