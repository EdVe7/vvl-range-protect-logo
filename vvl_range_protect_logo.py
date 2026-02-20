import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# 1. SETUP ESTETICO
st.set_page_config(page_title="V.V.L. Commander", page_icon="logo.png", layout="centered")

hide_ui = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_ui, unsafe_allow_html=True)

# 2. SPLASH SCREEN (SOLO LOGO)
if 'splash' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.write("Caricamento V.V.L. Commander...")
    time.sleep(3)
    placeholder.empty()
    st.session_state['splash'] = True

# 3. PASSWORD
if "auth" not in st.session_state:
    pwd = st.text_input("Inserisci Password", type="password")
    if st.button("Sblocca"):
        if pwd == "olimpiadi2040":
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Password Errata")
    st.stop()

# 4. CONNESSIONE DATI (IL FIX PER VEDERE I DATI VECCHI)
conn = st.connection("gsheets", type=GSheetsConnection)
# ttl=0 costringe l'app a scaricare TUTTO ogni volta, senza dimenticare i giorni passati
df = conn.read(ttl=0)

# Pulizia date: fondamentale per il filtro "Ultimi 7 giorni"
if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])

# 5. FORM INSERIMENTO
st.title("⛳ V.V.L. Range Commander")
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        bastone = st.selectbox("Bastone", ["Driver", "Legno 3", "Ibrido", "Ferro 4", "Ferro 5", "Ferro 6", "Ferro 7", "Ferro 8", "Ferro 9", "PW", "GW", "SW", "LW"])
        dist = st.number_input("Distanza (m)", value=0)
        voto = st.select_slider("Voto", options=[1, 2, 3, 4, 5], value=3)
    with col2:
        imp = st.selectbox("Impatto", ["Centro", "Punta", "Tacco", "Top", "Fatta"])
        err = st.selectbox("Errore", ["Dritto", "Hook", "L-Hook", "Slice", "L-Slice", "Push", "Pull"])
    
    if st.form_submit_button("REGISTRA COLPO 🚀"):
        nuovo = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Bastone": bastone, "Lunghezza": dist, "Impatto": imp, "Errore": err, "Voto": voto}])
        df_update = pd.concat([df, nuovo], ignore_index=True)
        conn.update(data=df_update)
        st.success("Salvato!")
        time.sleep(1)
        st.rerun()

# 6. ANALISI (QUELLA CHE TI PIACEVA)
if not df.empty:
    st.divider()
    scelta = st.radio("Periodo:", ["Tutti i dati", "Ultimi 7 giorni"], horizontal=True)
    
    if scelta == "Ultimi 7 giorni":
        limite = datetime.now() - timedelta(days=7)
        df_view = df[df['Data'] >= limite]
    else:
        df_view = df

    if not df_view.empty:
        # TABELLA CON DEVIAZIONE STANDARD (COSTANZA)
        st.subheader("📋 Performance")
        report = df_view.groupby('Bastone').agg({'Lunghezza': ['mean', 'std'], 'Voto': 'mean', 'Errore': lambda x: x.mode()[0] if not x.mode().empty else "-"}).reset_index()
        report.columns = ["Ferro", "Media Dist", "Costanza (Std)", "Voto Medio", "Errore Tipico"]
        st.dataframe(report.round(1).fillna(0), use_container_width=True, hide_index=True)

        # GRAFICI
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🍕 Voti %")
            fig_p = px.pie(df_view, names='Voto', hole=0.3, color_discrete_sequence=px.colors.sequential.Teal_r)
            st.plotly_chart(fig_p, use_container_width=True)
        with c2:
            st.subheader("🎯 Dispersione")
            map_err = {"Pull":-3, "Hook":-2, "L-Hook":-1, "Dritto":0, "L-Slice":1, "Slice":2, "Push":3}
            df_view['ex'] = df_view['Errore'].map(map_err)
            fig_s = px.scatter(df_view, x='ex', y='Lunghezza', color='Bastone', size='Voto')
            fig_s.update_xaxes(tickvals=[-3,-2,-1,0,1,2,3], ticktext=["Pull","Hook","LH","Dritto","LS","Slice","Push"])
            st.plotly_chart(fig_s, use_container_width=True)
