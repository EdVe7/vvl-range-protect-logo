import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime
import time
import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import tempfile
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 1. CONFIGURAZIONE E STILI
# ==============================================================================
st.set_page_config(page_title="V.V.L. Sport Science", page_icon="⛳", layout="wide")

COLORS = {
    'BrandTeal': '#3AB4B8',  
    'DarkTeal': '#2A8285',
    'Gold': '#DAA520', 
    'White': '#FFFFFF',
    'Grey': '#F3F4F6'
}

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
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("logo.png", use_container_width=True)
            except:
                st.markdown(f"<h1 style='text-align:center; font-size: 5rem; color:{COLORS['BrandTeal']};'>V.V.L.</h1><p style='text-align:center;'>SPORT SCIENCE SOLUTIONS</p>", unsafe_allow_html=True)
    time.sleep(2.0)
    placeholder.empty()
    st.session_state["splash_done"] = True

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo.png", width=200)
        except: pass
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
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def save_shot(shot_data):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_existing = load_data()
    df_new = pd.DataFrame([shot_data])
    df_final = pd.concat([df_existing, df_new], ignore_index=True)
    conn.update(data=df_final)
    st.cache_data.clear()

# ==============================================================================
# 5. GENERATORE GRAFICI SEABORN PER PDF
# ==============================================================================
def create_seaborn_pie(df, column, title):
    plt.figure(figsize=(6, 4))
    data = df[column].value_counts()
    colors = sns.color_palette("GnBu_d", len(data))
    plt.pie(data, labels=data.index, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 10})
    plt.title(title, fontsize=12, fontweight='bold', color=COLORS['DarkTeal'])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp.name, bbox_inches='tight', dpi=150)
    plt.close()
    return tmp.name

def create_seaborn_scatter(df, title):
    plt.figure(figsize=(8, 4))
    df_plot = df.copy()
    def calc_lat(row):
        if row['Direction'] == 'Dx': return row['Proximity']
        elif row['Direction'] == 'Sx': return -row['Proximity']
        return 0.0
    df_plot['Lateral_Error'] = df_plot.apply(calc_lat, axis=1)
    
    sns.scatterplot(data=df_plot, x='Lateral_Error', y='Club', hue='Club', s=100, palette="viridis", alpha=0.7)
    plt.axvline(0, color=COLORS['Gold'], linestyle='--', linewidth=2)
    plt.title(title, fontsize=12, fontweight='bold')
    plt.xlabel("Errore Laterale (Metri: Sx < 0 > Dx)")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp.name, bbox_inches='tight', dpi=150)
    plt.close()
    return tmp.name

# ==============================================================================
# 6. GENERATORE REPORT PDF (V.V.L. PRO)
# ==============================================================================
class PDFReport(FPDF):
    def header(self):
        try:
            self.image("logo.png", 10, 8, 33) # Logo in alto a sinistra
        except: pass
        self.set_font('Arial', 'B', 14)
        self.set_text_color(218, 165, 32)
        self.cell(0, 15, 'V.V.L. SPORT SCIENCE SOLUTIONS', 0, 1, 'R')
        self.set_draw_color(218, 165, 32)
        self.line(10, 32, 200, 32)
        self.ln(15) # Spazio dal logo/header al testo

def calc_perc(df, col, val):
    if len(df) == 0: return 0.0
    return (len(df[df[col] == val]) / len(df)) * 100

def generate_pro_pdf(df, user, period_name):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f"ANALISI PERFORMANCE ELITE - ATLETA: {user}", ln=True)
    pdf.cell(0, 6, f"PERIODO ANALISI: {period_name} | GENERATO IL: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    for cat in CATEGORIES:
        df_cat = df[df['Category'] == cat]
        if df_cat.empty: continue

        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(58, 180, 184)
        pdf.cell(0, 8, f" REPARTO: {cat} ", 0, 1, 'L', fill=True)
        pdf.set_text_color(0, 0, 0)
        
        # Statistiche testuali
        pdf.set_font('Arial', '', 9)
        pdf.ln(2)
        pdf.cell(0, 5, f"Volume: {len(df_cat)} colpi | Voto Medio: {df_cat['Rating'].mean():.2f}/3.0", ln=True)
        pdf.cell(0, 5, f"Efficienza (Voto 3): {calc_perc(df_cat, 'Rating', 3):.1f}%", ln=True)
        pdf.ln(5)

        # Inserimento Grafici Seaborn nel PDF
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(218, 165, 32)
        pdf.cell(0, 6, "DISTRIBUZIONE TECNICA E TENDENZE:", ln=True)
        
        # Grafico Impatti
        img_imp = create_seaborn_pie(df_cat, 'Impact', f"Qualita Impatto - {cat}")
        pdf.image(img_imp, x=15, y=pdf.get_y(), w=85)
        
        # Grafico Traiettorie
        img_curv = create_seaborn_pie(df_cat, 'Curvature', f"Tendenza Effetto - {cat}")
        pdf.image(img_curv, x=110, y=pdf.get_y(), w=85)
        pdf.set_y(pdf.get_y() + 65)

        # Spiegazione Grafici
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 4, "Interpretazione: I grafici a torta mostrano la consistenza del punto di impatto e la curvatura predominante. Uno slice/push costante indica un errore di cammino/faccia sistematico; impatti decentrati suggeriscono instabilita del raggio dell'arco di swing.")
        pdf.ln(5)

        if cat in ["LONG GAME / RANGE", "SHORT GAME"]:
            img_scat = create_seaborn_scatter(df_cat, f"Mappa Dispersione Laterale - {cat}")
            pdf.image(img_scat, x=30, y=pdf.get_y(), w=150)
            pdf.set_y(pdf.get_y() + 85)
            pdf.multi_cell(0, 4, "Mappa Dispersione: Rappresenta la distanza laterale dal target. L'obiettivo e raggruppare i punti sulla linea dorata (Target). Una dispersione ampia indica scarsa ripetibilita dinamica.")

        if pdf.get_y() > 230: pdf.add_page() # Salto pagina se spazio esaurito

    # Script Finale per l'Atleta
    pdf.ln(10)
    pdf.set_draw_color(58, 180, 184)
    pdf.set_fill_color(243, 244, 246)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(58, 180, 184)
    pdf.cell(0, 10, " MESSAGGIO DAL V.V.L. PERFORMANCE LAB ", 1, 1, 'C', fill=True)
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(42, 130, 133)
    script_text = (
        "Il talento fornisce la base, ma i dati costruiscono la vittoria. Analizzando i tuoi volumi, "
        "focalizzati sul trasformare i tuoi colpi 'Accettabili' in 'Esecuzioni Perfette' attraverso il controllo dell'impatto. "
        "La tua tendenza laterale e la chiave per il prossimo step tecnico. Torna in campo, la costanza e l'unica via."
    )
    pdf.multi_cell(0, 6, script_text, 0, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 7. INTERFACCIA APP PRINCIPALE
# ==============================================================================
st.sidebar.markdown(f"### Atleta: {st.session_state['user']}")
session_name = st.sidebar.text_input("Sessione / Note", "Test Valutazione")

tab_in, tab_an = st.tabs([" REGISTRO TELEMETRIA", " ANALYTICS & REPORT"])

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
                proximity = st.number_input("Proximity Target (metri)", min_value=0.0, step=1.0)
            voto = st.slider("Voto Esecuzione (1=Scarso, 2=Accettabile, 3=Perfetto)", 1, 3, 2)
            
        elif cat_scelta == "SHORT GAME":
            with col1:
                club = st.selectbox("Bastone", ["LW", "SW", "GW", "AW", "PW", "9i", "8i"])
                start_dist = st.number_input("Distanza di Partenza (metri)", min_value=1.0, step=1.0)
            with col2:
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
            with col1: start_dist = st.number_input("Distanza dal Buco (metri)", min_value=0.5, step=0.5)
            with col2: impact = st.selectbox("Impatto sulla Faccia", ["Centro", "Punta", "Tacco"])
            with col3: curvature = st.selectbox("Traiettoria / Linea", ["Dritta", "Push", "Pull"])
            proximity = st.number_input("Proximity (Distanza residua metri)", min_value=0.0, step=0.1)
            voto = st.slider("Voto (3=Buca/Perfetto, 2=Data, 1=Errore)", 1, 3, 2)

        if st.form_submit_button("SALVA COLPO NEL DATABASE"):
            shot = {
                'User': st.session_state['user'], 'Date': datetime.date.today(),
                'SessionName': session_name, 'Time': datetime.datetime.now().strftime("%H:%M"),
                'Category': cat_scelta, 'Club': club, 'Start_Dist': start_dist, 'Lie': lie,
                'Impact': impact, 'Curvature': curvature, 'Height': height,
                'Direction': direction, 'Proximity': proximity, 'Rating': voto
            }
            save_shot(shot)
            st.success("Metriche acquisite con successo.")

with tab_an:
    df_all = load_data()
    df_user = df_all[df_all['User'] == st.session_state['user']]
    periodo = st.selectbox("Filtro Temporale", ["Sessione Attuale", "Ultimi 7 Giorni", "Ultimi 30 Giorni", "Tutti i Dati"])
    oggi = datetime.date.today()
    if periodo == "Sessione Attuale": df_f = df_user[df_user['SessionName'] == session_name]
    elif periodo == "Ultimi 7 Giorni": df_f = df_user[df_user['Date'] >= (oggi - datetime.timedelta(days=7))]
    elif periodo == "Ultimi 30 Giorni": df_f = df_user[df_user['Date'] >= (oggi - datetime.timedelta(days=30))]
    else: df_f = df_user

    if not df_f.empty:
        pdf_bytes = generate_pro_pdf(df_f, st.session_state['user'], periodo)
        st.download_button(" SCARICA REPORT V.V.L. COMPLETO (PDF)", data=pdf_bytes, file_name=f"VVL_Report_{st.session_state['user']}.pdf", mime="application/pdf")
        st.divider()

        cat_grafici = st.radio("Dettaglio Grafici per Area", CATEGORIES, horizontal=True)
        df_p = df_f[df_f['Category'] == cat_grafici].copy()

        if not df_p.empty:
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-box'><div class='metric-title'>Voto Medio</div><div class='metric-value'>{df_p['Rating'].mean():.2f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-box'><div class='metric-title'>Colpi Registrati</div><div class='metric-value'>{len(df_p)}</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-box'><div class='metric-title'>Proximity Media</div><div class='metric-value'>{df_p['Proximity'].mean():.1f} m</div></div>", unsafe_allow_html=True)

            col_g1, col_g2 = st.columns(2)
            with col_g1: st.plotly_chart(px.pie(df_p, names='Impact', title="Analisi Impatti", hole=0.3, color_discrete_sequence=px.colors.sequential.Teal), use_container_width=True)
            with col_g2: st.plotly_chart(px.pie(df_p, names='Curvature', title="Analisi Traiettorie", hole=0.3, color_discrete_sequence=px.colors.sequential.Teal), use_container_width=True)
            
            if cat_grafici in ["LONG GAME / RANGE", "SHORT GAME"]:
                def calc_lateral(row):
                    if row['Direction'] == 'Dx': return row['Proximity']
                    elif row['Direction'] == 'Sx': return -row['Proximity']
                    return 0.0
                df_p['Lateral_Error'] = df_p.apply(calc_lateral, axis=1)
                fig_scatter = px.scatter(df_p, x='Lateral_Error', y='Club', color='Club', title="Dispersione Laterale", labels={'Lateral_Error': 'Sx <-- 0 --> Dx'})
                fig_scatter.add_vline(x=0, line_dash="dash", line_color=COLORS['Gold'])
                st.plotly_chart(fig_scatter, use_container_width=True)

if st.sidebar.button("LOGOUT / CAMBIA UTENTE"):
    st.session_state["logged_in"] = False
    st.rerun()
