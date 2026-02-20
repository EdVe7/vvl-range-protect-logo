import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURAZIONE PAGINA E RIMOZIONE MENU (FAVICON INCLUSA)
# ==========================================
st.set_page_config(
    page_title="V.V.L. Commander", 
    page_icon="logo.png", # Usa il tuo logo come vignetta dell'app
    layout="centered"
)

# Nasconde menu Streamlit, icona GitHub e footer per sembrare un'app nativa
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. SPLASH SCREEN (LOGO PER 3 SECONDI)
# ==========================================
if 'splash_done' not in st.session_state:
    splash_placeholder = st.empty()
    with splash_placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        try:
            st.image("logo.png", use_container_width=True)
        except:
            # Fallback se il logo non è ancora caricato su GitHub
            st.markdown("<h1 style='text-align: center; color: #2CB8C8;'>SPORT SCIENCE SOLUTIONS</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: gray;'>Target: Olimpiadi 2040</h3>", unsafe_allow_html=True)
        
    time.sleep(3)
    splash_placeholder.empty()
    st.session_state['splash_done'] = True

# ==========================================
# 3. SISTEMA DI ACCESSO CON PASSWORD
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Accesso Riservato</h2>", unsafe_allow_html=True)
        password = st.text_input("Inserisci la password per il V.V.L. Commander", type="password")
        if st.button("Accedi"):
            if password == "olimpiadi2040": # Password concordata
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Password errata.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 4. CONNESSIONE AL DATABASE (FIX CACHE E DATE)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# ttl=0 forza l'app a scaricare i dati nuovi ogni volta (Fix dati che non apparivano)
try:
    df = conn.read(ttl=0)
    if df.empty:
        df = pd.DataFrame(columns=["Data", "Bastone", "Lunghezza", "Impatto", "Errore", "Voto"])
    else:
        # Trasformiamo la colonna Data in formato temporale per i filtri
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.dropna(subset=['Data'])
except Exception as e:
    st.error("Errore di connessione. Controlla i Secrets!")
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
        nuovo_colpo = pd.DataFrame([{
            "Data": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Bastone": bastone,
            "Lunghezza": lunghezza,
            "Impatto": impatto,
            "Errore": errore,
            "Voto": voto
        }])
        df_aggiornato = pd.concat([df, nuovo_colpo], ignore_index=True)
        conn.update(data=df_aggiornato)
        st.success("✅ Colpo registrato nel Cloud!")
        time.sleep(1)
        st.rerun()

# ==========================================
# 6. ANALISI DEI DATI, GRAFICI E STATISTICHE
# ==========================================
if not df.empty:
    st.divider()
    
    # --- FILTRO TEMPORALE (Fix Filtro 7 Giorni) ---
    filtro = st.radio("Visualizzazione dati:", ["Tutti i tempi", "Ultimi 7 giorni"], horizontal=True)
    if filtro == "Ultimi 7 giorni":
        limite = datetime.now() - timedelta(days=7)
        df_view = df[df['Data'] >= limite]
    else:
        df_view = df

    if df_view.empty:
        st.info("Nessun dato presente per il periodo selezionato.")
    else:
        st.header("📊 Analisi e Statistiche")
        
        # --- TABELLA REPORT MEDIE E COSTANZA ---
        st.subheader("📋 Performance per Bastone")
        try:
            df_medie = df_view.groupby('Bastone').agg({
                'Lunghezza': ['mean', 'std'], # Media e Deviazione Standard (Costanza)
                'Voto': 'mean',
                'Impatto': lambda x: x.mode()[0] if not x.mode().empty else '-',
                'Errore': lambda x: x.mode()[0] if not x.mode().empty else '-'
            }).reset_index()
            
            # Pulizia nomi colonne
            df_medie.columns = ['Bastone', 'Media Dist (m)', 'Costanza (Dev.Std)', 'Voto Medio', 'Impatto Top', 'Errore Top']
            st.dataframe(df_medie.round(1).fillna(0), use_container_width=True, hide_index=True)
            st.caption("Più bassa è la 'Costanza', più i colpi sono simili tra loro (meglio!).")
        except:
            st.warning("Dati insufficienti per il calcolo delle medie.")

        # --- GRAFICO A TORTA DEI VOTI (%) ---
        st.subheader("🍕 Distribuzione Qualità Colpi")
        voti_count = df_view['Voto'].value_counts().reset_index()
        voti_count.columns = ['Voto', 'Numero Colpi']
        fig_pie = px.pie(voti_count, values='Numero Colpi', names='Voto', 
                         color_discrete_sequence=px.colors.sequential.Teal_r, hole=0.3)
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

        # --- GRAFICO DISPERSIONE (RIPRISTINATO) ---
        st.subheader("🎯 Mappa Dispersione")
        err_map = {"Pull": -3, "Hook": -2, "Leggero Hook": -1, "Dritto": 0, "Leggero Slice": 1, "Slice": 2, "Push": 3}
        df_view['Error_X'] = df_view['Errore'].map(err_map)
        
        fig_scatter = px.scatter(df_view, x='Error_X', y='Lunghezza', color='Bastone', size='Voto',
                                 hover_data=['Impatto', 'Errore'],
                                 labels={'Error_X': 'Dispersione (Sinistra <--> Destra)'})
        fig_scatter.update_xaxes(tickvals=[-3, -2, -1, 0, 1, 2, 3], 
                                 ticktext=["Pull", "Hook", "L-Hook", "Dritto", "L-Slice", "Slice", "Push"])
        st.plotly_chart(fig_scatter, use_container_width=True)

        with st.expander("Vedi ultimi 10 colpi inseriti"):
            st.dataframe(df_view.sort_values(by='Data', ascending=False).head(10), hide_index=True)