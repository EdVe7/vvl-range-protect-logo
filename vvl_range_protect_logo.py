import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime
import time
import numpy as np
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 1. CONFIGURAZIONE, COLORI E STILI (Teal, Gold, White)
# ==============================================================================
st.set_page_config(page_title="V.V.L. Commander Pro", page_icon="⛳", layout="wide")

COLORS = {
    'Teal': '#20B2AA',   
    'Gold': '#DAA520',   
    'White': '#FFFFFF',  
    'Red': '#DC2626',    
    'Grey': '#F9F9F9'    
}

st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .block-container {{ padding-top: 2rem; }}
    .stApp {{ background-color: {COLORS['White']}; color: #111827; }}
    h1, h2, h3 {{ font-family: 'Helvetica', sans-serif; color: {COLORS['Teal']}; }}
    .stButton>button {{ background-color: {COLORS['Teal']}; color: white; border-radius: 8px; font-weight: bold; width: 100%; border: none; padding: 10px; }}
    .metric-box {{ background: {COLORS['Grey']}; border-left: 5px solid {COLORS['Gold']}; border-radius: 5px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .metric-title {{ font-size: 0.9rem; color: #6b7280; text-transform: uppercase; font-weight: bold; }}
    .metric-value {{ font-size: 1.5rem; color: {COLORS['Teal']}; font-weight: 800; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. COSTANTI E OPZIONI
# ==============================================================================
COLUMNS = ['User', 'Date', 'SessionName', 'Time', 'Category', 'Club_Dist', 'Impact', 'Trajectory', 'Length_Speed', 'Proximity', 'Error_Dir', 'Rating']
CATEGORIES = ["LONG GAME", "SHORT GAME", "PUTTING"]

# ==============================================================================
# 3. SPLASH SCREEN & LOGIN
# ==============================================================================
if "splash_done" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
        <div style='background-color:{COLORS['Teal']}; height:90vh; display:flex; flex-direction:column; align-items:center; justify-content:center; border-radius:15px;'>
            <h1 style='color:{COLORS['White']}; font-size: 4rem; margin-bottom:0;'>V.V.L.</h1>
            <h2 style='color:{COLORS['Gold']}; font-size: 1.5rem; margin-top:0;'>COMMANDER PRO ANALYTICS</h2>
        </div>
        """, unsafe_allow_html=True)
    time.sleep(2)
    placeholder.empty()
    st.session_state["splash_done"] = True

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔒 Area Riservata V.V.L.")
    user_input = st.text_input("Nome Atleta").upper().strip()
    pass_input = st.text_input("Password", type="password")
    if st.button("ACCEDI"):
        if pass_input == "olimpiadi2040" and user_input != "":
            st.session_state["logged_in"] = True
            st.session_state["user"] = user_input
            st.rerun()
        else:
            st.error("Credenziali non valide.")
    st.stop()

# ==============================================================================
# 4. DATA ENGINE (Google Sheets)
# ==============================================================================
@st.cache_data(ttl=5) # Aggiorna i dati ogni 5 secondi
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        # Assicuriamoci che la colonna Date sia in formato datetime per i filtri
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
        return pd.DataFrame(columns=COLUMNS)

def save_shot(shot_data):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_existing = load_data()
    df_new = pd.DataFrame([shot_data])
    df_final = pd.concat([df_existing, df_new], ignore_index=True)
    conn.update(data=df_final)
    st.cache_data.clear()

# ==============================================================================
# 5. GENERATORE PDF PROFESSIONALE
# ==============================================================================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(32, 178, 170) # Teal
        self.cell(0, 10, 'V.V.L. COMMANDER - PERFORMANCE REPORT', 0, 1, 'C')
        self.set_draw_color(218, 165, 32) # Gold
        self.line(10, 20, 200, 20)
        self.ln(10)

def generate_pdf(df, user, period_name):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Atleta: {user} | Periodo Analizzato: {period_name} | Data Report: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    for cat in CATEGORIES:
        df_cat = df[df['Category'] == cat]
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(218, 165, 32) # Gold
        pdf.cell(0, 10, f"ANALISI: {cat}", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        if df_cat.empty:
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 8, "Nessun dato registrato in questo periodo.", ln=True)
            pdf.ln(5)
            continue
            
        tot = len(df_cat)
        avg_rating = df_cat['Rating'].mean()
        std_dev = df_cat['Rating'].std() if tot > 1 else 0.0
        err_comune = df_cat['Error_Dir'].mode()[0] if not df_cat['Error_Dir'].empty and df_cat['Error_Dir'].mode()[0] != "-" else "N/A"
        prox_comune = df_cat['Proximity'].mode()[0] if not df_cat['Proximity'].empty and df_cat['Proximity'].mode()[0] != "-" else "N/A"
        perc_top = (len(df_cat[df_cat['Rating'] == 3]) / tot) * 100

        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"- Colpi Totali: {tot}", ln=True)
        pdf.cell(0, 6, f"- Media Voto: {avg_rating:.2f} / 3.0  (Deviazione Standard: {std_dev:.2f})", ln=True)
        pdf.cell(0, 6, f"- Esecuzioni Perfette (Voto 3): {perc_top:.1f}%", ln=True)
        pdf.cell(0, 6, f"- Errore Direzionale più frequente: {err_comune}", ln=True)
        pdf.cell(0, 6, f"- Proximity tipica / più frequente: {prox_comune}", ln=True)
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 6. INTERFACCIA UTENTE PRINCIPALE
# ==============================================================================
st.sidebar.title(f"👤 {st.session_state['user']}")
session_name = st.sidebar.text_input("Nome Sessione", "Allenamento Standard")

tab_in, tab_an = st.tabs(["📥 INSERIMENTO DATI", "📊 ANALISI & REPORT"])

# --- TAB 1: INSERIMENTO ---
with tab_in:
    cat_scelta = st.selectbox("Seleziona Area di Gioco", CATEGORIES)
    
    with st.form("form_inserimento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        if cat_scelta == "LONG GAME":
            with col1:
                club = st.selectbox("Bastone", ["Driver", "Legni", "Ibridi", "Ferri Lunghi", "Ferri Corti", "Wedges"])
                impact = st.selectbox("Impatto", ["Solido", "Top", "Flappa", "Tacco", "Punta", "Shank"])
            with col2:
                traj = st.selectbox("Traiettoria", ["Dritta", "Draw", "Fade", "Pull", "Push", "Hook", "Slice"])
                length = st.selectbox("Lunghezza", ["Giusta", "Corta", "Lunga"])
            prox = st.selectbox("Proximity (Distanza dal Target)", ["< 2m", "< 5m", "< 10m", "> 10m"])
            err_dir = st.selectbox("Direzione Errore Principale", ["Nessuno (Target)", "Sinistra", "Destra"])
            voto = st.slider("Voto Esecuzione", 1, 3, 2)
            
        elif cat_scelta == "SHORT GAME":
            with col1:
                club = st.selectbox("Bastone", ["LW", "SW", "GW", "AW", "PW", "F9", "F8"])
                impact = st.selectbox("Impatto", ["Solido", "Top", "Flappa", "Shank"])
            with col2:
                traj = st.selectbox("Lie di Partenza", ["Fairway", "Rough", "Bunker", "Sponda"]) # Usiamo traj per il Lie
                length = st.selectbox("Controllo Distanza", ["Giusta", "Corta", "Lunga"])
            prox = st.selectbox("Proximity (Risultato)", ["Data (<1m)", "Vicino (<3m)", "Ok (<5m)", "Fuori (<10m)"])
            err_dir = "-"
            voto = st.slider("Voto Esecuzione", 1, 3, 2)
            
        else: # PUTTING
            club = st.selectbox("Distanza Iniziale", ["1m", "2m", "3m", "5m", "8m", "10m", ">15m"])
            with col1:
                impact = st.selectbox("Impatto", ["Centro", "Punta", "Tacco"])
                traj = st.selectbox("Linea", ["Corretta", "Push (Dx)", "Pull (Sx)"])
            with col2:
                length = st.selectbox("Velocità", ["Perfetta", "Corta", "Lunga"])
                prox = st.selectbox("Proximity Finale", ["Imbucato", "Data (<50cm)", "Lungo (>1m)", "Corto (>1m)"])
            err_dir = "-"
            voto = st.slider("Voto Esecuzione (3=Buca, 2=Data, 1=Errore)", 1, 3, 2)

        if st.form_submit_button("REGISTRA COLPO"):
            nuovo_colpo = {
                'User': st.session_state['user'],
                'Date': datetime.date.today(),
                'SessionName': session_name,
                'Time': datetime.datetime.now().strftime("%H:%M"),
                'Category': cat_scelta,
                'Club_Dist': club,
                'Impact': impact,
                'Trajectory': traj,
                'Length_Speed': length,
                'Proximity': prox,
                'Error_Dir': err_dir,
                'Rating': voto
            }
            save_shot(nuovo_colpo)
            st.success("✅ Colpo registrato nel database!")

# --- TAB 2: ANALISI ---
with tab_an:
    df_all = load_data()
    df_user = df_all[df_all['User'] == st.session_state['user']]
    
    # Filtro Temporale
    periodo = st.radio("Seleziona Periodo di Analisi", ["Sessione Attuale", "Ultima Settimana", "Ultimo Mese", "Ultimo Anno", "Lifelong (Tutto)"], horizontal=True)
    
    oggi = datetime.date.today()
    if periodo == "Sessione Attuale":
        df_filtered = df_user[df_user['SessionName'] == session_name]
    elif periodo == "Ultima Settimana":
        df_filtered = df_user[df_user['Date'] >= (oggi - datetime.timedelta(days=7))]
    elif periodo == "Ultimo Mese":
        df_filtered = df_user[df_user['Date'] >= (oggi - datetime.timedelta(days=30))]
    elif periodo == "Ultimo Anno":
        df_filtered = df_user[df_user['Date'] >= (oggi - datetime.timedelta(days=365))]
    else:
        df_filtered = df_user

    if df_filtered.empty:
        st.warning("Nessun dato trovato per questo periodo/sessione.")
    else:
        # Download Report PDF
        pdf_bytes = generate_pdf(df_filtered, st.session_state['user'], periodo)
        st.download_button(label="📄 SCARICA REPORT PDF PROFESSIONALE", data=pdf_bytes, file_name=f"Report_{st.session_state['user']}_{periodo.replace(' ', '')}.pdf", mime="application/pdf")
        st.divider()

        # Analisi Visiva per Categoria (SOLO TORTE)
        cat_analisi = st.selectbox("Seleziona Area per i Grafici", CATEGORIES)
        df_plot = df_filtered[df_filtered['Category'] == cat_analisi]
        
        if not df_plot.empty:
            c1, c2, c3 = st.columns(3)
            media = df_plot['Rating'].mean()
            std = df_plot['Rating'].std() if len(df_plot) > 1 else 0.0
            
            with c1: st.markdown(f"<div class='metric-box'><div class='metric-title'>Media Voto</div><div class='metric-value'>{media:.2f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-box'><div class='metric-title'>Deviazione Std.</div><div class='metric-value'>{std:.2f}</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-box'><div class='metric-title'>Colpi Totali</div><div class='metric-value'>{len(df_plot)}</div></div>", unsafe_allow_html=True)

            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Torta dei Voti
                fig_voti = px.pie(df_plot, names='Rating', hole=0.4, 
                                  color='Rating', color_discrete_map={1: COLORS['Red'], 2: COLORS['Gold'], 3: COLORS['Teal']},
                                  title="Distribuzione Qualità (Voti)")
                fig_voti.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_voti, use_container_width=True)
                
            with col_chart2:
                # Torta degli Impatti
                fig_impatti = px.pie(df_plot, names='Impact', hole=0.4,
                                     title="Distribuzione Tipologia Impatto")
                fig_impatti.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_impatti, use_container_width=True)
        else:
            st.info(f"Nessun colpo registrato in {cat_analisi} per il periodo selezionato.")

if st.sidebar.button("ESCI"):
    st.session_state["logged_in"] = False
    st.rerun()
