import streamlit as st
import pandas as pd
from datetime import date

# Configuración de la página
st.set_page_config(page_title="Calculadora de Cheques - Miguel Andrada", layout="wide")

# --- ENCABEZADO PERSONALIZADO ---
st.title("🏦 Calculadora de Cheques")
st.markdown("<p style='font-size:18px; color: #555555; margin-top:-20px;'>C.P. Miguel Andrada</p>", unsafe_allow_html=True)
st.divider()

# --- CONFIGURACIÓN EN SIDEBAR ---
with st.sidebar:
    st.header("Configuración de Tasas")
    base_dias = st.selectbox("Base de cálculo anual", [360, 365], index=0)
    iva_pct = st.number_input("IVA (%)", value=10.5, step=0.5)
    perc_iva_pct = st.number_input("Percepción IVA (%)", value=1.5, step=0.1)
    
    st.subheader("Grilla de Tasas por Plazo")
    data_tasas = {
        "Días Hasta": [6, 15, 30, 60, 90, 180, 360],
        "TNA %": [25.0, 26.0, 28.0, 31.0, 32.0, 36.0, 39.0]
    }
    df_tasas = st.data_editor(pd.DataFrame(data_tasas), num_rows="dynamic")

# --- ENTRADA DE DATOS DE LA OPERACIÓN ---
col1, col2 = st.columns(2)
with col1:
    modo = st.radio("Operación:", 
                    ["Calcular Neto (¿Cuánto recibo?)", 
                     "Calcular Nominal (¿De cuánto debe ser el cheque?)"])
    monto_input = st.number_input("Monto de referencia ($)", min_value=0.0, value=5000000.0, step=10000.0)

with col2:
    f_hoy = st.date_input("Fecha de Negociación", date.today())
    f_pago = st.date_input("Fecha de Pago (Vencimiento)", date(2026, 5, 31))

# Cálculo de días
dias_plazo = (f_pago - f_hoy).days

if dias_plazo <= 0:
    st.error("⚠️ La fecha de pago debe ser posterior a la de negociación.")
else:
    # Selección automática de Tasa según el plazo
    tasa_anual = df_tasas["TNA %"].iloc[-1]
    for i, row in df_tasas.iterrows():
        if dias_plazo <= row["Días Hasta"]:
            tasa_anual = row["TNA %"]
            break
    
    # Constantes de cálculo
    t_p = (tasa_anual / 100) * (dias_plazo / base_dias)
    impuestos_factor = (iva_pct + perc_iva_pct) / 100
    
    if "¿Cuánto recibo?" in modo:
        v_nominal = monto_input
        intereses = v_nominal * t_p
        iva = intereses * (iva_pct / 100)
        perc = intereses * (perc_iva_pct / 100)
        v_neto = v_nominal - intereses - iva - perc
    else:
        v_neto = monto_input
        # Fórmula inversa para hallar el Nominal partiendo del Neto deseado
        v_nominal = v_neto / (1 - (t_p * (1 + impuestos_factor)))
        intereses = v_nominal * t_p
        iva = intereses * (iva_pct / 100)
        perc = intereses * (perc_iva_pct / 100)

    # --- PRESENTACIÓN DE RESULTADOS ---
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("ACREDITADO NETO", f"$ {v_neto:,.2f}")
    res_col2.metric("VALOR NOMINAL", f"$ {v_nominal:,.2f}")
    res_col3.metric("TNA (%)", f"{tasa_anual}%")

    st.subheader("Liquidación Detallada")
    detalle = pd.DataFrame({
        "Concepto": [
            "(+) Valor Nominal del Cheque", 
            "(-) Intereses Bancarios", 
            "(-) IVA sobre Intereses", 
            "(-) Percepción IVA", 
            "(=) TOTAL NETO ACREDITADO"
        ],
        "Monto": [v_nominal, -intereses, -iva, -perc, v_neto]
    })
    
    st.table(detalle.style.format({"Monto": "$ {:,.2f}"}))
    st.info(f"Liquidación calculada para {dias_plazo} días de plazo, utilizando base anual de {base_dias} días.")
