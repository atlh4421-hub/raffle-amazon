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

# --- CONFIGURATION ---
IMAP_SERVER = "imap.mail.me.com"
PASSWORD = "btyd-sevh-vioq-hxca"  # Ton mot de passe d'application iCloud activé
# ---------------------

# Interface de l'application
st.title("🎉 Amazon Raffle Tracker")
st.write("Suivez vos victoires quotidiennes en temps réel.")

# Inputs pour l'utilisateur
email_user = st.text_input("Votre adresse email iCloud :", placeholder="exemple@icloud.com")
jours_arriere = st.slider("Nombre de jours à analyser :", min_value=1, max_value=7, value=1)
mot_cle = st.text_input("Mot-clé dans le sujet (ex: gagné, félicitations) :", value="gagné")

# Fonction de récupération des mails
def fetch_raffles(email_addr, days, keyword):
    wins = []
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(email_addr, PASSWORD)
        mail.select("inbox")

        # Calcul de la date limite de recherche
        date_target = (datetime.date.today() - datetime.timedelta(days=days-1)).strftime("%d-%b-%Y")
        
        # Recherche des mails Amazon depuis la date cible
        status, messages = mail.search(None, f'(SINCE "{date_target}" FROM "amazon")')
        
        if status != "OK":
            return False, "Erreur lors de la recherche des emails."

        email_ids = messages[0].split()
        
        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Décoder le sujet
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # Filtrer par mot-clé
                    if keyword.lower() not in subject.lower():
                        continue

                    # Récupérer la date de l'email
                    email_date = msg["Date"]

                    # Extraire le corps
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

                    # Extraction du nom de l'article (Regex ajustable)
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
        return False, "Identifiants incorrects. Vérifiez votre adresse email."
    except Exception as e:
        return False, f"Erreur de connexion : {str(e)}"

# Bouton d'action sur mobile
if st.button("🔄 Actualiser les victoires", use_container_width=True):
    if not email_user:
        st.warning("⚠️ Veuillez entrer votre adresse email iCloud.")
    else:
        with st.spinner("Analyse de votre boîte mail en cours..."):
            success, result = fetch_raffles(email_user, jours_arriere, mot_cle)
            
            if success:
                if len(result) == 0:
                    st.info("Aucune victoire trouvée pour cette période. Continuez d'y croire ! 💪")
                else:
                    st.success(f"🎉 {len(result)} victoire(s) détectée(s) !")
                    for idx, win in enumerate(result, 1):
                        # Création de jolies cartes d'affichage
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
