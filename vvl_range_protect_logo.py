import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURAZIONE E LOOK (Vignetta e UI)
# ==========================================
st.set_page_config(
    page_title="V.V.L. Commander", 
    page_icon="logo.png", 
    layout="centered"
)

# Nasconde menu Streamlit, icona GitHub e footer
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
# 2. SPLASH SCREEN (SOLO LOGO PER 3 SECONDI)
# ==========================================
if 'splash_done' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Tenta di caricare il logo. Se non lo trova, non scrive nulla (rimane bianco)
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown("<h2 style='text-align:center;'>Caricamento...</h2>", unsafe_allow_html=True)
    
    time.sleep(3)
    placeholder.empty()
    st.session_state['splash_done'] = True

# ==========================================
# 3. SISTEMA DI ACCESSO CON PASSWORD
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h3 style='text-align:center;'>🔒 Accesso Riservato</h3>", unsafe_allow_html=True)
        pwd = st.text_input("Password", type="password")
        if st.button("Entra nel Commander"):
            if pwd == "olimpiadi2040": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Accesso negato")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 4. CONNESSIONE DATI (Fix Cache & Inattività)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0) # ttl=0 forza la lettura dei dati nuovi ogni volta

if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])

# ==========================================
# 5. INTERFACCIA UTENTE PRINCIPALE
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
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Bastone": bastone,
            "Lunghezza": lunghezza,
            "Impatto": impatto,
            "Errore": errore,
            "Voto": voto
        }])
        df_aggiornato = pd.concat([df, nuovo_colpo], ignore_index=True)
        conn.update(data=df_aggiornato)
        st.success("✅ Colpo registrato!")
        time.sleep(1)
        st.rerun()

# ==========================================
# 6. ANALISI, MEDIE E GRAFICI
# ==========================================
if not df.empty:
    st.divider()
    periodo = st.radio("Filtro:", ["Tutti i tempi", "Ultimi 7 giorni"], horizontal=True)
    
    if periodo == "Ultimi 7 giorni":
        limite = datetime.now() - timedelta(days=7)
        df_view = df[df['Data'] >= limite]
    else:
        df_view = df

    if not df_view.empty:
        st.header("📊 Statistiche")
        
        # TABELLA MEDIE E COSTANZA
        report = df_view.groupby('Bastone').agg({
            'Lunghezza': ['mean', 'std'],
            'Voto': 'mean',
            'Impatto': lambda x: x.mode()[0] if not x.mode().empty else "-",
            'Errore': lambda x: x.mode()[0] if not x.mode().empty else "-"
        }).reset_index()
        report.columns = ["Ferro", "Media Dist (m)", "Dev. Standard (Costanza)", "Voto Medio", "Impatto Top", "Errore Top"]
        st.dataframe(report.round(1).fillna(0), use_container_width=True, hide_index=True)

        # GRAFICO A TORTA
        st.subheader("🍕 Qualità Colpi (%)")
        voti_count = df_view['Voto'].value_counts().reset_index()
        voti_count.columns = ['Voto', 'Conteggio']
        fig_pie = px.pie(voti_count, values='Conteggio', names='Voto', hole=0.3, color_discrete_sequence=px.colors.sequential.Teal_r)
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

        # GRAFICO DISPERSIONE
        st.subheader("🎯 Mappa Dispersione")
        err_map = {"Pull": -3, "Hook": -2, "Leggero Hook": -1, "Dritto": 0, "Leggero Slice": 1, "Slice": 2, "Push": 3}
        df_view['Error_X'] = df_view['Errore'].map(err_map)
        fig_scatter = px.scatter(df_view, x='Error_X', y='Lunghezza', color='Bastone', size='Voto', hover_data=['Impatto', 'Errore'])
        fig_scatter.update_xaxes(tickvals=[-3, -2, -1, 0, 1, 2, 3], ticktext=["Pull", "Hook", "L-Hook", "Dritto", "L-Slice", "Slice", "Push"])
        st.plotly_chart(fig_scatter, use_container_width=True)
