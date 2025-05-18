import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

st.set_page_config(page_title="Dashboard Kas ASDP", layout="wide")

# ===== Autentikasi Google Sheets =====
import json
from oauth2client.service_account import ServiceAccountCredentials
from io import StringIO

SERVICE_ACCOUNT = json.loads(st.secrets["SERVICE_ACCOUNT"])

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT, scope)
client = gspread.authorize(credentials)

# ===== Fungsi load data dari Google Sheets =====
def load_sheet(sheet_name):
    sheet = client.open("Update Giro 2025").worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# ===== Ambil data dari sheet =====
df_giro = load_sheet("Giro")
df_depo = load_sheet("Deposito")
df_cashflow = load_sheet("Cashflow")

# ===== Filter sidebar =====
st.sidebar.header("Filter")
bulan = st.sidebar.selectbox("Bulan", sorted(df_giro['Bulan'].unique()))
tahun = st.sidebar.selectbox("Tahun", sorted(df_giro['Tahun'].unique()))
keterangan = st.sidebar.multiselect("Keterangan", df_giro['Keterangan'].unique(), default=df_giro['Keterangan'].unique())

# ===== Filter data =====
df_giro_f = df_giro[(df_giro['Bulan'] == bulan) & (df_giro['Tahun'] == tahun) & (df_giro['Keterangan'].isin(keterangan))]
df_depo_f = df_depo[(df_depo['Bulan'] == bulan) & (df_depo['Tahun'] == tahun) & (df_depo['Keterangan'].isin(keterangan))]

# ===== Tampilan utama =====
st.title("📊 Dashboard Kas dan Setara Kas - ASDP")

col1, col2 = st.columns(2)

# --- Giro ---
with col1:
    st.subheader("Total Saldo Giro per Bank")
    total_giro = df_giro_f.groupby("Bank")["Saldo Akhir"].sum().reset_index()
    st.dataframe(total_giro)

    fig_giro = px.pie(total_giro, names="Bank", values="Saldo Akhir", title="Proporsi Saldo Giro per Bank")
    st.plotly_chart(fig_giro)

# --- Deposito ---
with col2:
    st.subheader("Total Saldo Deposito per Bank")
    total_depo = df_depo_f.groupby("Bank")["Saldo Akhir"].sum().reset_index()
    st.dataframe(total_depo)

    rate_min = float(df_depo_f["Rate"].min())
    rate_max = float(df_depo_f["Rate"].max())
    rate_slider = st.slider("Filter berdasarkan Rate Deposito", min_value=rate_min, max_value=rate_max, step=0.25)
    filtered_depo = df_depo_f[df_depo_f["Rate"] >= rate_slider]
    pie_depo = px.pie(filtered_depo.groupby("Bank")["Saldo Akhir"].sum().reset_index(), names="Bank", values="Saldo Akhir", title="Proporsi Deposito (Rate ≥ " + str(rate_slider) + ")")
    st.plotly_chart(pie_depo)

# --- Cashflow Chart ---
st.subheader("📈 Grafik Cash In & Cash Out per Bulan")
df_cash = df_cashflow.groupby(["Bulan", "Jenis"])["Jumlah"].sum().reset_index()
fig_cashflow = px.line(df_cash, x="Bulan", y="Jumlah", color="Jenis", markers=True, title="Cash In dan Cash Out Bulanan")
st.plotly_chart(fig_cashflow, use_container_width=True)
