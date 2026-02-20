import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURAZIONE E BRANDING
# ==========================================
# Cambia 'logo.png' con l'URL della tua immagine o il percorso locale
LOGO_PATH = "logo.png" 
PRIMARY_COLOR = "#1E5631"  # Verde Golf Professionale
ACCENT_COLOR = "#D4AF37"   # Oro/Sabbia per i dettagli

st.set_page_config(
    page_title="V.V.L. Commander", 
    page_icon="⛳", 
    layout="wide", # Layout largo per vedere meglio i grafici
    initial_sidebar_state="collapsed"
)

# CSS Custom per iniettare i tuoi colori nell'interfaccia
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa; }}
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 10px;
        border: none;
        height: 3em;
        width: 100%;
    }}
    .stMetric {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
    }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SPLASH SCREEN OTTIMIZZATO
# ==========================================
if 'splash_done' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns([1,2,1])
        with col_s2:
            # Mostra logo se esiste, altrimenti titolo stilizzato
            try:
                st.image(LOGO_PATH, use_container_width=True)
            except:
                st.markdown(f"<h1 style='text-align: center; color: {PRIMARY_COLOR};'>V.V.L. COMMANDER</h1>", unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='text-align: center; color: {ACCENT_COLOR};'>Target: Olimpiadi 2040</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Inizializzazione sistema di puntamento...</p>", unsafe_allow_html=True)
            progress_bar = st.progress(0)
            for percent_complete in range(100):
                time.sleep(0.02)
                progress_bar.progress(percent_complete + 1)
    
    placeholder.empty()
    st.session_state['splash_done'] = True

# ==========================================
# 3. LOGICA DI ACCESSO
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("### 🔒 Area Riservata")
            password = st.text_input("Inserisci la password di comando", type="password")
            if st.button("Sblocca Database"):
                if password == "olimpiadi2040":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Accesso negato.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 4. CONNESSIONE DATI
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df = conn.read()
except Exception as e:
    st.error("Connessione Cloud non riuscita. Verifica i Secrets.")
    st.stop()

# ==========================================
# 5. DASHBOARD PRINCIPALE
# ==========================================
# Sidebar per inserimento rapido
with st.sidebar:
    try: st.image(LOGO_PATH, width=150)
    except: st.title("⛳ V.V.L.")
    st.header("Nuova Registrazione")
    with st.form("golf_form", clear_on_submit=True):
        bastone = st.selectbox("Bastone", ["Driver", "Legno 3", "Ibrido", "Ferro 4", "Ferro 5", "Ferro 6", "Ferro 7", "Ferro 8", "Ferro 9", "PW", "GW", "SW", "LW"])
        lunghezza = st.number_input("Distanza (m)", min_value=0, step=1)
        impatto = st.selectbox("Impatto", ["Centro", "Punta", "Tacco", "Top", "Zolla"])
        errore = st.selectbox("Traiettoria", ["Dritto", "Draw", "Fade", "Hook", "Slice", "Push", "Pull"])
        voto = st.select_slider("Qualità", options=[1, 2, 3, 4, 5], value=3)
        
        submit = st.form_submit_button("REGISTRA COLPO")
        if submit:
            nuovo_colpo = pd.DataFrame([{
                "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                "Bastone": bastone, "Lunghezza": lunghezza, "Impatto": impatto, "Errore": errore, "Voto": voto
            }])
            df_aggiornato = pd.concat([df, nuovo_colpo], ignore_index=True)
            conn.update(data=df_aggiornato)
            st.success("Dato inviato!")
            time.sleep(1)
            st.rerun()

# --- Area Visualizzazione ---
st.title("📊 Analisi Performance Operativa")

if not df.empty:
    # KPI Veloci
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Colpi Totali", len(df))
    col_m2.metric("Distanza Max", f"{df['Lunghezza'].max()} m")
    col_m3.metric("Voto Medio", f"{round(df['Voto'].mean(), 1)} / 5")

    tab1, tab2 = st.tabs(["📈 Analisi Tecnica", "📋 Registro Storico"])

    with tab1:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Distanza Media per Bastone")
            # Grafico a barre orizzontali professionale
            avg_dist = df.groupby('Bastone')['Lunghezza'].mean().sort_values().reset_index()
            fig_bar = px.bar(avg_dist, x='Lunghezza', y='Bastone', orientation='h',
                             color_continuous_scale='Greens', color='Lunghezza',
                             text_auto='.0f')
            fig_bar.update_layout(showlegend=False, height=400, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            st.subheader("Distribuzione Precisione")
            error_count = df['Errore'].value_counts().reset_index()
            fig_pie = px.pie(error_count, values='count', names='Errore', hole=.4,
                             color_discrete_sequence=px.colors.sequential.Greens_r)
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)

else:
    st.info("Inizia a registrare i tuoi colpi dalla barra laterale per vedere le statistiche.")
