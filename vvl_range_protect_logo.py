import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURAZIONE PAGINA E RIMOZIONE MENU GITHUB
# ==========================================
st.set_page_config(page_title="V.V.L. Commander", page_icon="logo.png", layout="centered")

# Questo blocco nasconde il menu in alto a destra (i tre puntini e l'icona GitHub) e il footer
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. SPLASH SCREEN (LOGO PER 3 SECONDI)
# ==========================================
# Se la variabile 'splash_done' non esiste, mostriamo il logo
if 'splash_done' not in st.session_state:
    splash_placeholder = st.empty() # Crea un contenitore vuoto
    with splash_placeholder.container():
        st.markdown("<h1 style='text-align: center; margin-top: 50px;'>V.V.L. COMMANDER</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: gray;'>Target: Olimpiadi 2040</h3>", unsafe_allow_html=True)
        
        # INSERISCI QUI IL NOME DEL TUO LOGO CARICATO SU GITHUB. 
        # Se non hai ancora il file, commenta la riga qui sotto aggiungendo un # all'inizio
        # st.image("logo.png", use_container_width=True) 
        
    time.sleep(3) # Pausa di 3 secondi
    splash_placeholder.empty() # Svuota il contenitore e fa sparire il logo
    st.session_state['splash_done'] = True # Segna che lo splash è stato mostrato

# ==========================================
# 3. SISTEMA DI ACCESSO CON PASSWORD
# ==========================================
def check_password():
    """Restituisce True se l'utente ha inserito la password corretta."""
    if "password_correct" not in st.session_state:
        st.warning("🔒 Inserisci la password per accedere al database.")
        password = st.text_input("Password", type="password")
        if st.button("Accedi"):
            if password == "olimpiadi2040": # <--- CAMBIA QUI LA TUA PASSWORD
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Password errata.")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop() # Ferma l'app qui se la password non è inserita

# ==========================================
# 4. CONNESSIONE AL DATABASE (GOOGLE SHEETS)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# Proviamo a leggere i dati esistenti
try:
    df = conn.read()
    # Se il foglio è vuoto, creiamo una struttura di base
    if df.empty:
        df = pd.DataFrame(columns=["Data", "Bastone", "Lunghezza", "Impatto", "Errore", "Voto"])
except Exception as e:
    st.error("Errore di connessione a Google Sheets. Controlla i Secrets!")
    st.stop()

# ==========================================
# 5. INTERFACCIA UTENTE: INSERIMENTO COLPI
# ==========================================
st.title("⛳ V.V.L. Range Commander")

with st.form("golf_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        bastone = st.selectbox("Bastone", ["Driver", "Legno 3", "Ibrido", "Ferro 4", "Ferro 5", "Ferro 6", "Ferro 7", "Ferro 8", "Ferro 9", "PW", "GW", "SW", "LW"])
        lunghezza = st.number_input("Lunghezza (metri)", min_value=0, max_value=400, step=1)
        voto = st.slider("Voto Colpo (1-5)", min_value=1, max_value=5, value=3)
    
    with col2:
        impatto = st.selectbox("Impatto sulla faccia", ["Centro", "Punta", "Tacco", "Top", "Fatta (Zolla)"])
        errore = st.selectbox("Dispersione/Errore", ["Dritto", "Leggero Hook", "Hook", "Leggero Slice", "Slice", "Push", "Pull"])
        
    submit = st.form_submit_button("REGISTRA COLPO 🚀")

    if submit:
        # Prepara il nuovo colpo
        nuovo_colpo = pd.DataFrame([{
            "Data": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Bastone": bastone,
            "Lunghezza": lunghezza,
            "Impatto": impatto,
            "Errore": errore,
            "Voto": voto
        }])
        
        # Aggiunge il colpo al database esistente
        df_aggiornato = pd.concat([df, nuovo_colpo], ignore_index=True)
        # Salva su Google Sheets
        conn.update(worksheet="Foglio1", data=df_aggiornato) # Assicurati che il nome del foglio sia corretto
        st.success("✅ Colpo registrato nel Cloud!")
        st.rerun()

# ==========================================
# 6. ANALISI DEI DATI E GRAFICI
# ==========================================
if not df.empty:
    st.divider()
    st.header("📊 Analisi e Statistiche")
    
    # --- TABELLA REPORT MEDIE PER BASTONE ---
    st.subheader("📋 Report Medio per Bastone")
    # Calcoliamo le medie per i numeri e troviamo il valore più frequente (mode) per i testi
    try:
        df_medie = df.groupby('Bastone').agg({
            'Lunghezza': 'mean',
            'Voto': 'mean',
            'Impatto': lambda x: x.mode()[0] if not x.mode().empty else '-',
            'Errore': lambda x: x.mode()[0] if not x.mode().empty else '-'
        }).reset_index()
        
        # Arrotondiamo i numeri per renderli leggibili
        df_medie['Lunghezza'] = df_medie['Lunghezza'].round(1)
        df_medie['Voto'] = df_medie['Voto'].round(1)
        
        # Rinominiamo le colonne
        df_medie.columns = ['Bastone', 'Lunghezza Media (m)', 'Voto Medio', 'Impatto Più Frequente', 'Errore Frequente']
        st.dataframe(df_medie, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning("Non ci sono ancora abbastanza dati per generare la tabella delle medie.")

    st.divider()

    # --- GRAFICO A TORTA DEI VOTI ---
    st.subheader("🍕 Distribuzione Voti")
    # Contiamo quanti colpi ci sono per ogni voto
    voti_count = df['Voto'].value_counts().reset_index()
    voti_count.columns = ['Voto', 'Numero Colpi']
    
    fig_pie = px.pie(voti_count, values='Numero Colpi', names='Voto', 
                     title="Percentuale Voti Ricevuti",
                     color_discrete_sequence=px.colors.sequential.Teal)
    st.plotly_chart(fig_pie, use_container_width=True)

    # Mostriamo gli ultimi colpi grezzi
    with st.expander("Vedi tutti i colpi registrati"):
        st.dataframe(df.tail(10)) # Mostra gli ultimi 10

