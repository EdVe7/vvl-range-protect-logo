import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import datetime
import time
import os
import numpy as np
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 1. CONFIGURAZIONE & STILI
# ==============================================================================
st.set_page_config(page_title="V.V.L. Commander Pro", page_icon="⛳", layout="centered")

# ==============================================================================
# MODIFICA SOLO QUESTI VALORI PER CAMBIARE I COLORI DI TUTTA L'APP
# ==============================================================================
COLORS = {
    'Navy': '#20B2AA',       # Verde Acqua (usato per Header e Splash)
    'Green': '#20B2AA',      # Verde Acqua (usato per i successi/Putting)
    'Orange': '#DAA520',     # Oro scuro (usato per Short Game)
    'Blue': '#40E0D0',       # Turchese/Verde Acqua chiaro (usato per il Range)
    'Red': '#DC2626',        # Rosso (rimane per gli errori critici/Shank)
    'Grey': '#F9F9F9',       # Bianco sporco/Grigio chiarissimo per gli sfondi
    'Gold': '#FFD700',       # Oro brillante (usato per accenti e stelle)
    'White': '#FFFFFF'       # Bianco puro
} 


# --- SOSTITUISCI IL VECCHIO st.markdown CON QUESTO ---

st.markdown(f"""
<style>
    /* 1. NASCONDE GLI ELEMENTI DI SISTEMA (GITHUB, MENU, FOOTER) */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* 2. REGOLA LO SPAZIO IN ALTO */
    .block-container {{
        padding-top: 2rem;
    }}

    /* 3. STILE GENERALE APP (BIANCO E COLORI LOGO) */
    .stApp {{ 
        background-color: #FFFFFF; 
        color: #111827; 
    }}
    
    h1, h2, h3 {{ 
        font-family: 'Helvetica', sans-serif; 
        color: #20B2AA; /* Verde Acqua */
    }}
    
    /* 4. STILE RADIO BUTTONS (BOTTONI SCELTA) */
    div[role="radiogroup"] label {{
        font-size: 15px !important; 
        padding: 8px 12px;
        background-color: #F9F9F9; /* Bianco sporco */
        border-radius: 6px; 
        margin: 3px;
        border: 1px solid #e5e7eb;
    }}
    
    /* Effetto al passaggio del mouse sui bottoni */
    div[role="radiogroup"] label:hover {{ 
        border-color: #20B2AA; 
        background-color: #f0fdfa; 
    }}
    
    /* 5. STILE BOTTONE PRINCIPALE DI REGISTRAZIONE */
    .stButton>button {{
        color: white; 
        font-size: 20px !important; 
        padding: 12px 0;
        border-radius: 8px; 
        font-weight: bold; 
        width: 100%; 
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}

    /* 6. STILE BOX STATISTICHE (METRICHE) */
    .metric-box {{
        background: white; 
        border: 1px solid #e5e7eb; 
        border-radius: 8px;
        padding: 15px; 
        text-align: center; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .metric-num {{ 
        font-size: 1.8rem; 
        font-weight: 800; 
        color: #20B2AA; /* Verde Acqua */
    }}
    .metric-lbl {{ 
        font-size: 0.8rem; 
        text-transform: uppercase; 
        color: #DAA520; /* Oro */
        letter-spacing: 0.5px;
    }}
</style>
""", unsafe_allow_html=True)

# Liste Costanti
CLUBS_FULL = ['Driver', 'Legno 3', 'Legno 5', 'Legno 7', 'Ibrido', 'Ferro 2', 'Ferro 3', 'Ferro 4', 'Ferro 5', 'Ferro 6', 'Ferro 7', 'Ferro 8', 'Ferro 9', 'PW', 'AW', 'GW', 'SW', 'LW']
CLUBS_WEDGE = ['LW', 'SW', 'GW', 'AW', 'PW', 'Ferro 9', 'Ferro 8']
DISTANCES_PUTT = ['1m', '2m', '3m', '4m', '5m', '6m', '8m', '10m', '12m', '15m', '20m', '>20m']
PROXIMITY_RANGE = ["< 2m (Target)", "< 5m", "< 10m", "> 10m"]
PROXIMITY_SG = ["Given (<1m)", "Close (<3m)", "Ok (<5m)", "On Green (<10m)", "Miss (>10m)"]
DIR_ERROR = ["Dritta (Target)", "Sinistra (Pull/Hook)", "Destra (Push/Slice)"]
DB_COLUMNS = ['User', 'Date', 'SessionName', 'Time', 'Mode', 'Param1', 'Param2', 'Param3', 'Param4', 'Param5', 'Param6', 'Voto']

# ==============================================================================
# 2. LOGICA DI ACCESSO & SPLASH SCREEN
# ==============================================================================
if "splash_done" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
        <div style='background-color:{COLORS['Navy']}; height:90vh; display:flex; flex-direction:column; align-items:center; justify-content:center; border-radius:15px;'>
            <h1 style='color:white; font-size: 3.5rem; margin-bottom:0;'>V.V.L.</h1>
            <h2 style='color:{COLORS['Gold']}; font-size: 1.5rem; margin-top:0;'>COMMANDER PRO</h2>
            <div style='width: 50px; height: 50px; border: 5px solid {COLORS['Grey']}; border-top: 5px solid {COLORS['Gold']}; border-radius: 50%; animation: spin 1s linear infinite;'></div>
            <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
        </div>
        """, unsafe_allow_html=True)
    time.sleep(3)
    placeholder.empty()
    st.session_state["splash_done"] = True

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔒 Accesso Riservato")
    with st.container():
        user_input = st.text_input("Nome Atleta", placeholder="Es: MARIO ROSSI").upper().strip()
        pass_input = st.text_input("Password di Sistema", type="password")
        if st.button("SBLOCCA COMMANDER"):
            if pass_input == "olimpiadi2040" and user_input != "":
                st.session_state["logged_in"] = True
                st.session_state["username"] = user_input
                st.rerun()
            else:
                st.error("Credenziali non valide.")
    st.stop()

# ==============================================================================
# 3. ENGINE DATI (GOOGLE SHEETS)
# ==============================================================================
def get_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=DB_COLUMNS)
        return df
    except:
        return pd.DataFrame(columns=DB_COLUMNS)

def save_data(new_row_dict):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_existing = get_data()
    df_new = pd.DataFrame([new_row_dict])
    df_final = pd.concat([df_existing, df_new], ignore_index=True)
    conn.update(data=df_final)

# ==============================================================================
# 4. REPORT PDF GENERATOR
# ==============================================================================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, 'V.V.L. COMMANDER PERFORMANCE REPORT', 0, 1, 'C')
        self.ln(5)

def create_pdf(df, user, mode):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"Atleta: {user} | Modalità: {mode} | Data: {datetime.date.today()}", ln=True)
    
    # Statistiche % nel Report
    total = len(df)
    avg = df['Voto'].mean()
    perc_3 = (len(df[df['Voto'] == 3]) / total * 100) if total > 0 else 0
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f"KPI: Media Voto: {avg:.2f} | Colpi Top (3/3): {perc_3:.1f}%", ln=True)
    pdf.ln(5)
    
    # Tabella Semplificata
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(40, 7, "Data", 1)
    pdf.cell(40, 7, "Param 1", 1)
    pdf.cell(40, 7, "Impatto", 1)
    pdf.cell(30, 7, "Voto", 1)
    pdf.ln()
    
    pdf.set_font('Arial', '', 8)
    for _, row in df.tail(20).iterrows():
        pdf.cell(40, 6, str(row['Date']), 1)
        pdf.cell(40, 6, str(row['Param1']), 1)
        pdf.cell(40, 6, str(row['Param2']), 1)
        pdf.cell(30, 6, str(row['Voto']), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 5. UI PRINCIPALE
# ==============================================================================
st.sidebar.title(f"👤 {st.session_state['username']}")
mode = st.sidebar.radio("MODALITÀ", ["RANGE", "SHORT GAME", "PUTTING"])
session_name = st.sidebar.text_input("Nome Sessione", "Allenamento Standard")

tab_in, tab_an = st.tabs(["📥 Inserimento Colpo", "📊 Analisi Dati"])

# --- TAB INSERIMENTO ---
with tab_in:
    with st.form("shot_form", clear_on_submit=True):
        st.subheader(f"Registra Colpo: {mode}")
        c1, c2 = st.columns(2)
        
        if mode == "RANGE":
            with c1:
                p1 = st.selectbox("Bastone", CLUBS_FULL)
                p2 = st.radio("Impatto", ["Solido", "Top", "Flappa", "Tacco", "Punta", "Shank"])
            with c2:
                p3 = st.radio("Volo", ["Dritta", "Draw", "Fade", "Push", "Pull", "Hook", "Slice"])
                p4 = st.radio("Lunghezza", ["Giusta", "Corta", "Lunga"])
            p5 = st.select_slider("Proximity", options=PROXIMITY_RANGE)
            p6 = st.radio("Direzione Errore", DIR_ERROR, horizontal=True)
            rating = st.slider("Voto Colpo", 1, 3, 2)
            
        elif mode == "SHORT GAME":
            with c1:
                p1 = st.selectbox("Bastone", CLUBS_WEDGE)
                p2 = st.radio("Impatto", ["Solido", "Flappa", "Top", "Shank"])
            with c2:
                p3 = st.selectbox("Lie", ["Fairway", "Rough", "Bunker", "Sponda"])
                p4 = st.radio("Controllo", ["Giusta", "Corta", "Lunga"])
            p5 = st.select_slider("Proximity", options=PROXIMITY_SG)
            p6 = "-"
            rating = st.radio("Voto", [1, 2, 3], horizontal=True)

        else: # PUTTING
            p1 = st.select_slider("Distanza", options=DISTANCES_PUTT)
            with c1:
                p2 = st.radio("Impatto", ["Centro", "Punta", "Tacco"])
                p3 = st.radio("Linea", ["Dritta", "Push (Dx)", "Pull (Sx)"])
            with c2:
                p4 = st.radio("Velocità", ["Giusta", "Corta", "Lunga"])
                rating = st.radio("Esito", [1, 2, 3], format_func=lambda x: "3 (Imbucato)" if x==3 else ("2 (Data)" if x==2 else "1 (Errore)"))
            p5, p6 = "-", "-"

        if st.form_submit_button("REGISTRA NEL DATABASE"):
            shot_data = {
                'User': st.session_state['username'], 'Date': str(datetime.date.today()),
                'SessionName': session_name, 'Time': datetime.datetime.now().strftime("%H:%M"),
                'Mode': mode, 'Param1': p1, 'Param2': p2, 'Param3': p3, 'Param4': p4,
                'Param5': p5, 'Param6': p6, 'Voto': rating
            }
            save_data(shot_data)
            st.toast("Colpo salvato correttamente!", icon="⛳")

# --- TAB ANALISI ---
with tab_an:
    df_all = get_data()
    # FILTRO RAZIONALE: Solo dati dell'utente loggato
    df_user = df_all[df_all['User'] == st.session_state['username']]
    df_mode = df_user[df_user['Mode'] == mode]

    if df_mode.empty:
        st.warning("Nessun dato disponibile per questo profilo in questa modalità.")
    else:
        # KPI
        avg_v = df_mode['Voto'].astype(float).mean()
        st.markdown(f"### Analisi Performance {mode}")
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.metric("Colpi Totali", len(df_mode))
        c_k2.metric("Voto Medio", f"{avg_v:.2f}")
        c_k3.metric("Affidabilità", f"{(avg_v/3*100):.1f}%")

        st.divider()

        # GRAFICO A TORTA DEI VOTI (Richiesto)
        st.subheader("Distribuzione Qualità Colpi (Voti)")
        fig_voti = px.pie(df_mode, names='Voto', hole=0.4, 
                          color='Voto', color_discrete_map={1: COLORS['Red'], 2: COLORS['Orange'], 3: COLORS['Green']},
                          title="Percentuale Voti Ricevuti")
        st.plotly_chart(fig_voti, use_container_width=True)

        # GRAFICO IMPATTI
        st.subheader("Analisi Tipologia Impatto")
        fig_imp = px.bar(df_mode.groupby('Param2').size().reset_index(name='count'), 
                         x='Param2', y='count', color='Param2', title="Frequenza Tipi di Impatto")
        st.plotly_chart(fig_imp, use_container_width=True)

        # DOWNLOAD REPORT
        st.divider()
        pdf_bytes = create_pdf(df_mode, st.session_state['username'], mode)
        st.download_button("📥 SCARICA REPORT PDF PROFESSIONALE", data=pdf_bytes, 
                           file_name=f"Report_{st.session_state['username']}_{mode}.pdf", mime="application/pdf")

if st.sidebar.button("LOGOUT"):
    st.session_state["logged_in"] = False
    st.rerun()


