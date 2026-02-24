import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime
import time
import os
import numpy as np
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 1. CONFIGURAZIONE E STILI (Colori VVL: Teal, Gold, White)
# ==============================================================================
st.set_page_config(page_title="V.V.L. Sport Science", page_icon="⛳", layout="wide")

COLORS = {
    'BrandTeal': '#3AB4B8',  
    'DarkTeal': '#2A8285',
    'Gold': '#DAA520',       # Aggiunto l'Oro richiesto
    'White': '#FFFFFF',
    'Grey': '#F3F4F6'
}

# CSS aggressivo per nascondere qualsiasi elemento di GitHub/Streamlit
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden; display: none;}}
    header {{visibility: hidden; display: none;}}
    footer {{visibility: hidden; display: none;}}
    [data-testid="stToolbar"] {{visibility: hidden; display: none;}}
    [data-testid="stDecoration"] {{visibility: hidden; display: none;}}
    .block-container {{ padding-top: 1rem; }}
    .stApp {{ background-color: {COLORS['White']}; color: #1f2937; }}
    h1, h2, h3 {{ font-family: 'Helvetica', sans-serif; color: {COLORS['BrandTeal']}; }}
    .stButton>button {{ background-color: {COLORS['BrandTeal']}; color: white; border-radius: 8px; font-weight: bold; width: 100%; border: none; padding: 12px; }}
    .stButton>button:hover {{ background-color: {COLORS['DarkTeal']}; }}
    .metric-box {{ background: {COLORS['Grey']}; border-left: 4px solid {COLORS['Gold']}; border-radius: 4px; padding: 15px; text-align: center; }}
    .metric-title {{ font-size: 0.85rem; color: #6b7280; text-transform: uppercase; font-weight: bold; }}
    .metric-value {{ font-size: 1.8rem; color: {COLORS['BrandTeal']}; font-weight: 800; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. COSTANTI DATI
# ==============================================================================
COLUMNS = ['User', 'Date', 'SessionName', 'Time', 'Category', 'Club', 'Start_Dist', 'Lie', 'Impact', 'Curvature', 'Height', 'Direction', 'Proximity', 'Rating']
CATEGORIES = ["LONG GAME / RANGE", "SHORT GAME", "PUTTING"]
CLUBS = ["DR", "3W", "5W", "7W", "3H", "3i", "4i", "5i", "6i", "7i", "8i", "9i", "PW", "AW", "GW", "SW", "LW"]

# ==============================================================================
# 3. SPLASH SCREEN & LOGIN
# ==============================================================================
if "splash_done" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                from PIL import Image
                img = Image.open("logo.png")
                st.image(img, use_container_width=True)
            except:
                st.markdown(f"<h1 style='text-align:center; font-size: 5rem; color:{COLORS['BrandTeal']};'>V.V.L.</h1><p style='text-align:center;'>SPORT SCIENCE SOLUTIONS</p>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; margin-top:20px;'>Caricamento Moduli Analitici...</div>", unsafe_allow_html=True)
    time.sleep(2.0)
    placeholder.empty()
    st.session_state["splash_done"] = True

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            from PIL import Image
            st.image(Image.open("logo.png"), width=200)
        except:
            pass
        st.markdown("### Accesso Piattaforma Pro")
        user_input = st.text_input("ID Atleta (Nome)").upper().strip()
        pass_input = st.text_input("Master Password", type="password")
        if st.button("AUTENTICAZIONE"):
            if pass_input == "v.v.l.analytics" and user_input != "":
                st.session_state["logged_in"] = True
                st.session_state["user"] = user_input
                st.rerun()
            else:
                st.error("Credenziali respinte.")
    st.stop()

# ==============================================================================
# 4. DATA ENGINE (Google Sheets)
# ==============================================================================
@st.cache_data(ttl=5)
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        df['Proximity'] = pd.to_numeric(df['Proximity'], errors='coerce')
        return df
    except Exception as e:
        return pd.DataFrame(columns=COLUMNS)

def save_shot(shot_data):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_existing = load_data()
    df_new = pd.DataFrame([shot_data])
    df_final = pd.concat([df_existing, df_new], ignore_index=True)
    conn.update(data=df_final)
    st.cache_data.clear()

# ==============================================================================
# 5. GENERATORE REPORT PDF (Con dettagli ORO)
# ==============================================================================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(218, 165, 32) # Gold VVL per il titolo principale
        self.cell(0, 8, 'V.V.L. SPORT SCIENCE - ANALISI BIOMECCANICA E PERFORMANCE', 0, 1, 'C')
        self.set_draw_color(218, 165, 32) # Linea Gold
        self.line(10, 18, 200, 18)
        self.ln(5)

def calc_perc(df, col, val):
    if len(df) == 0: return 0.0
    return (len(df[df[col] == val]) / len(df)) * 100

def generate_pro_pdf(df, user, period_name):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f"ATLETA: {user}   |   PERIODO: {period_name}   |   DATA: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    for cat in CATEGORIES:
        df_cat = df[df['Category'] == cat]
        if df_cat.empty: continue

        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(58, 180, 184) # Teal Background
        pdf.cell(0, 8, f" REPARTO: {cat} ", 0, 1, 'L', fill=True)
        pdf.set_text_color(0, 0, 0)
        
        tot = len(df_cat)
        avg_voto = df_cat['Rating'].mean()
        
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 6, f"Volumi Sessione: {tot} colpi | Voto Medio: {avg_voto:.2f}/3.0 | Esecuzioni Perfette (Voto 3): {calc_perc(df_cat, 'Rating', 3):.1f}%", ln=True)
        
        if cat in ["LONG GAME / RANGE", "SHORT GAME"]:
            pdf.cell(0, 5, f"Impatti: Solido {calc_perc(df_cat, 'Impact', 'Solido'):.1f}% | Punta {calc_perc(df_cat, 'Impact', 'Punta'):.1f}% | Tacco {calc_perc(df_cat, 'Impact', 'Tacco'):.1f}% | Flappa {calc_perc(df_cat, 'Impact', 'Flappa'):.1f}%", ln=True)
            pdf.cell(0, 5, f"Traiettorie: Dritta {calc_perc(df_cat, 'Curvature', 'Dritta'):.1f}% | Slice {calc_perc(df_cat, 'Curvature', 'Slice'):.1f}% | Hook {calc_perc(df_cat, 'Curvature', 'Hook'):.1f}% | Push {calc_perc(df_cat, 'Curvature', 'Push'):.1f}%", ln=True)
            
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(218, 165, 32) # Sottotitolo in Gold
            pdf.cell(0, 6, "ANALISI DETTAGLIATA PER BASTONE (Medie e Tendenze):", ln=True)
            pdf.set_text_color(0, 0, 0) # Torna nero
            pdf.set_font('Arial', '', 8)
            clubs_used = df_cat['Club'].unique()
            for c in clubs_used:
                df_c = df_cat[df_cat['Club'] == c]
                if not df_c.empty:
                    m_voto = df_c['Rating'].mean()
                    m_prox = df_c['Proximity'].mean()
                    top_imp = df_c['Impact'].mode()[0] if not df_c['Impact'].empty else "N/A"
                    top_curv = df_c['Curvature'].mode()[0] if not df_c['Curvature'].empty else "N/A"
                    perc_dritta = calc_perc(df_c, 'Curvature', 'Dritta')
                    pdf.cell(0, 5, f" > {c}: {len(df_c)} colpi | Voto: {m_voto:.1f} | Prox Media: {m_prox:.1f}m | Tendenza Effetto: {top_curv} (Dritte: {perc_dritta:.0f}%) | Impatto Frequente: {top_imp}", ln=True)

        elif cat == "PUTTING":
            pdf.cell(0, 5, f"Impatti: Centro {calc_perc(df_cat, 'Impact', 'Centro'):.1f}% | Punta {calc_perc(df_cat, 'Impact', 'Punta'):.1f}% | Tacco {calc_perc(df_cat, 'Impact', 'Tacco'):.1f}%", ln=True)
            pdf.cell(0, 5, f"Traiettoria (Linea): Dritta {calc_perc(df_cat, 'Curvature', 'Dritta'):.1f}% | Push {calc_perc(df_cat, 'Curvature', 'Push'):.1f}% | Pull {calc_perc(df_cat, 'Curvature', 'Pull'):.1f}%", ln=True)
            
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(218, 165, 32) # Sottotitolo in Gold
            pdf.cell(0, 6, "ANALISI DETTAGLIATA PER DISTANZA INIZIALE:", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 8)
            dists = df_cat['Start_Dist'].unique()
            for d in sorted(dists):
                df_d = df_cat[df_cat['Start_Dist'] == d]
                if not df_d.empty:
                    m_voto = df_d['Rating'].mean()
                    top_traj = df_d['Curvature'].mode()[0] if not df_d['Curvature'].empty else "N/A"
                    perc_buca = calc_perc(df_d, 'Rating', 3)
                    pdf.cell(0, 5, f" > Da {d}m: {len(df_d)} putts | Voto Medio: {m_voto:.1f} | Imbucati: {perc_buca:.0f}% | Errore Linea Frequente: {top_traj}", ln=True)
        pdf.ln(8)
    
    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 6. INTERFACCIA APP PRINCIPALE
# ==============================================================================
st.sidebar.markdown(f"### 👤 Atleta: {st.session_state['user']}")
session_name = st.sidebar.text_input("Sessione / Note", "Test Valutazione")

tab_in, tab_an = st.tabs(["🎯 REGISTRO TELEMETRIA", "📊 ANALYTICS & REPORT"])

# --- TAB 1: INSERIMENTO DATI ---
with tab_in:
    cat_scelta = st.radio("Seleziona Area Tecnica", CATEGORIES, horizontal=True)
    
    with st.form("form_dati", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        start_dist = 0.0; lie = "-"; height = "-"; direction = "-"

        if cat_scelta == "LONG GAME / RANGE":
            with col1:
                club = st.selectbox("Bastone", CLUBS)
                impact = st.selectbox("Impatto", ["Solido", "Punta", "Tacco", "Shank", "Flappa", "Top"])
            with col2:
                curvature = st.selectbox("Curvatura (Effetto)", ["Dritta", "Push", "Pull", "Slice", "Hook"])
                height = st.selectbox("Altezza", ["Giusta", "Alta", "Bassa", "Rasoterra", "Flappa"])
            with col3:
                direction = st.selectbox("Direzione vs Target", ["Dritta", "Dx", "Sx"])
                proximity = st.number_input("Proximity Target (metri)", min_value=0.0, max_value=400.0, step=1.0)
            voto = st.slider("Voto Esecuzione (1=Scarso, 2=Accettabile, 3=Perfetto)", 1, 3, 2)
            
        elif cat_scelta == "SHORT GAME":
            with col1:
                club = st.selectbox("Bastone", ["LW", "SW", "GW", "AW", "PW", "9i", "8i"])
                start_dist = st.number_input("Distanza di Partenza (metri)", min_value=1.0, max_value=100.0, step=1.0)
            with col2:
                # Rimosso "Collo" come richiesto
                lie = st.selectbox("Lie", ["Fairway", "Rough", "Bunker", "Sponda"])
                impact = st.selectbox("Impatto", ["Solido", "Punta", "Tacco", "Shank", "Flappa", "Top"])
            with col3:
                curvature = st.selectbox("Curvatura Volo", ["Dritta", "Push", "Pull", "Slice", "Hook"])
                height = st.selectbox("Altezza", ["Giusta", "Alta", "Bassa", "Rasoterra", "Flappa"])
            
            c_bot1, c_bot2 = st.columns(2)
            direction = c_bot1.selectbox("Direzione vs Target", ["Dritta", "Dx", "Sx"])
            proximity = c_bot2.number_input("Proximity Finale (metri)", min_value=0.0, step=0.5)
            voto = st.slider("Voto Esecuzione (1=Scarso, 2=Accettabile, 3=Perfetto)", 1, 3, 2)
            
        else: # PUTTING
            club = "Putter"
            with col1:
                start_dist = st.number_input("Distanza dal Buco (metri)", min_value=0.5, step=0.5)
            with col2:
                impact = st.selectbox("Impatto sulla Faccia", ["Centro", "Punta", "Tacco"])
            with col3:
                curvature = st.selectbox("Traiettoria / Linea", ["Dritta", "Push", "Pull"])
            
            proximity = st.number_input("Proximity (Distanza residua in metri, 0 se in buca)", min_value=0.0, step=0.1)
            voto = st.slider("Voto (3=Buca/Perfetto, 2=Data/Accettabile, 1=Errore)", 1, 3, 2)

        if st.form_submit_button("SALVA COLPO NEL DATABASE"):
            shot = {
                'User': st.session_state['user'], 'Date': datetime.date.today(),
                'SessionName': session_name, 'Time': datetime.datetime.now().strftime("%H:%M"),
                'Category': cat_scelta, 'Club': club, 'Start_Dist': start_dist, 'Lie': lie,
                'Impact': impact, 'Curvature': curvature, 'Height': height,
                'Direction': direction, 'Proximity': proximity, 'Rating': voto
            }
            save_shot(shot)
            st.success("✅ Metriche acquisite con successo.")

# --- TAB 2: ANALISI & DASHBOARD ---
with tab_an:
    df_all = load_data()
    df_user = df_all[df_all['User'] == st.session_state['user']]
    
    periodo = st.selectbox("Filtro Temporale", ["Sessione Attuale", "Ultimi 7 Giorni", "Ultimi 30 Giorni", "Tutti i Dati (Lifelong)"])
    oggi = datetime.date.today()
    if periodo == "Sessione Attuale": df_f = df_user[df_user['SessionName'] == session_name]
    elif periodo == "Ultimi 7 Giorni": df_f = df_user[df_user['Date'] >= (oggi - datetime.timedelta(days=7))]
    elif periodo == "Ultimi 30 Giorni": df_f = df_user[df_user['Date'] >= (oggi - datetime.timedelta(days=30))]
    else: df_f = df_user

    if df_f.empty:
        st.warning("Nessun dato registrato nel periodo selezionato.")
    else:
        pdf_bytes = generate_pro_pdf(df_f, st.session_state['user'], periodo)
        st.download_button("📄 SCARICA REPORT V.V.L. COMPLETO (PDF)", data=pdf_bytes, file_name=f"VVL_Report_{st.session_state['user']}.pdf", mime="application/pdf")
        st.divider()

        cat_grafici = st.radio("Dettaglio Grafici per Area", CATEGORIES, horizontal=True)
        # Usiamo .copy() per evitare warning quando creiamo l'assegnazione per lo scatter plot
        df_p = df_f[df_f['Category'] == cat_grafici].copy()

        if not df_p.empty:
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-box'><div class='metric-title'>Voto Medio</div><div class='metric-value'>{df_p['Rating'].mean():.2f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-box'><div class='metric-title'>Colpi Registrati</div><div class='metric-value'>{len(df_p)}</div></div>", unsafe_allow_html=True)
            with c3: 
                prox_mean = df_p['Proximity'].mean()
                st.markdown(f"<div class='metric-box'><div class='metric-title'>Proximity Media</div><div class='metric-value'>{prox_mean:.1f} m</div></div>", unsafe_allow_html=True)

            # Grafici a torta originali preservati
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_imp = px.pie(df_p, names='Impact', title="Analisi Impatti", hole=0.3, color_discrete_sequence=px.colors.sequential.Teal)
                st.plotly_chart(fig_imp, use_container_width=True)
            with col_g2:
                fig_curv = px.pie(df_p, names='Curvature', title="Analisi Traiettorie/Effetti", hole=0.3, color_discrete_sequence=px.colors.sequential.Teal)
                st.plotly_chart(fig_curv, use_container_width=True)
            
            # NUOVO GRAFICO: Mappa di Dispersione Laterale
            if cat_grafici in ["LONG GAME / RANGE", "SHORT GAME"]:
                st.divider()
                st.markdown(f"<h3 style='text-align:center; color:{COLORS['DarkTeal']};'>🎯 Mappa di Dispersione Laterale</h3>", unsafe_allow_html=True)
                
                # Calcolo della dispersione laterale: Sx diventa negativo, Dx positivo
                def calc_lateral(row):
                    if row['Direction'] == 'Dx': return row['Proximity']
                    elif row['Direction'] == 'Sx': return -row['Proximity']
                    else: return 0.0 # Dritta
                
                df_p['Lateral_Error'] = df_p.apply(calc_lateral, axis=1)
                
                fig_scatter = px.scatter(df_p, x='Lateral_Error', y='Club', color='Club',
                                         title="Dispersione per Bastone (Metri dal Target)",
                                         labels={'Lateral_Error': 'Errore Laterale (Sx <-- 0 --> Dx)', 'Club': 'Bastone Utilizzato'},
                                         hover_data=['Curvature', 'Impact', 'Rating'],
                                         color_discrete_sequence=px.colors.qualitative.Bold)
                
                # Aggiunge la linea rossa tratteggiata centrale che rappresenta il Target
                fig_scatter.add_vline(x=0, line_dash="dash", line_color=COLORS['Gold'], annotation_text="TARGET", annotation_position="top right")
                fig_scatter.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                
                st.plotly_chart(fig_scatter, use_container_width=True)
                
        else:
            st.info("Dati insufficienti in questa categoria per generare i grafici.")

if st.sidebar.button("LOGOUT / CAMBIA UTENTE"):
    st.session_state["logged_in"] = False
    st.rerun()


