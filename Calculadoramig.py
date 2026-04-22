import streamlit as st
import pandas as pd
from datetime import date

# Configuración visual
st.set_page_config(page_title="Calculadora Bancaria - C.P. Miguel Andrada", layout="wide")

# --- ESTILO CSS PARA LA FIRMA (AHORA A LA IZQUIERDA) ---
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: #555555;
        text-align: left; /* Cambiado a la izquierda */
        padding: 10px 25px;
        font-weight: bold;
        font-size: 14px;
        border-top: 1px solid #e6e6e6;
        z-index: 100;
    }
    </style>
    <div class="footer">
        C.P. Miguel Andrada
    </div>
    """,
    unsafe_allow_html=True
)

st.title("🏦 Calculadora de Cheques -  C.P. Miguel Andrada")

# --- CONFIGURACIÓN EN SIDEBAR ---
with st.sidebar:
    st.header("Configuración")
    base_dias = st.selectbox("Base de cálculo anual", [360, 365], index=0)
    iva_pct = st.number_input("IVA (%)", value=10.5, step=0.5)
    perc_iva_pct = st.number_input("Percepción IVA (%)", value=1.5, step=0.1)
    
    st.subheader("Grilla de Tasas")
    data_tasas = {
        "Días Hasta": [6, 15, 30, 60, 90, 180, 360],
        "TNA %": [25.0, 26.0, 28.0, 31.0, 32.0, 36.0, 39.0]
    }
    df_tasas = st.data_editor(pd.DataFrame(data_tasas), num_rows="dynamic")

# --- ENTRADA DE DATOS ---
col1, col2 = st.columns(2)
with col1:
    modo = st.radio("¿Qué operación desea realizar?", 
                    ["Calcular Neto (Partiendo del Nominal)", 
                     "Calcular Nominal (Para llegar a un Neto)"])
    monto_input = st.number_input("Monto de referencia ($)", min_value=0.0, value=5000000.0, step=10000.0)

with col2:
    f_hoy = st.date_input("Fecha de Negociación", date.today())
    f_pago = st.date_input("Fecha de Pago (Vencimiento)", date(2026, 5, 31))

dias_plazo = (f_pago - f_hoy).days

if dias_plazo <= 0:
    st.error("⚠️ La fecha de pago debe ser posterior a la de negociación.")
else:
    # Selección de Tasa por tramo
    tasa_anual = df_tasas["TNA %"].iloc[-1]
    for i, row in df_tasas.iterrows():
        if dias_plazo <= row["Días Hasta"]:
            tasa_anual = row["TNA %"]
            break
    
    # Cálculo de factores
    t_p = (tasa_anual / 100) * (dias_plazo / base_dias)
    impuestos_factor = (iva_pct + perc_iva_pct) / 100
    
    if "Partiendo del Nominal" in modo:
        v_nominal = monto_input
        intereses = v_nominal * t_p
        iva = intereses * (iva_pct / 100)
        perc = intereses * (perc_iva_pct / 100)
        v_neto = v_nominal - intereses - iva - perc
    else:
        v_neto = monto_input
        v_nominal = v_neto / (1 - (t_p * (1 + impuestos_factor)))
        intereses = v_nominal * t_p
        iva = intereses * (iva_pct / 100)
        perc = intereses * (perc_iva_pct / 100)

    # --- RESULTADOS VISUALES ---
    st.divider()
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("ACREDITADO NETO", f"$ {v_neto:,.2f}")
    res_col2.metric("VALOR NOMINAL", f"$ {v_nominal:,.2f}")
    res_col3.metric("TNA APLICADA", f"{tasa_anual}%")

    st.subheader("Liquidación Detallada")
    detalle = pd.DataFrame({
        "Concepto": ["(+) Valor Nominal del Cheque", "(-) Intereses Bancarios", "(-) IVA sobre Intereses", "(-) Percepción IVA", "(=) TOTAL NETO ACREDITADO"],
        "Monto": [v_nominal, -intereses, -iva, -perc, v_neto]
    })
    
    st.table(detalle.style.format({"Monto": "$ {:,.2f}"}))
    st.info(f"Cálculo realizado con base de {base_dias} días anuales para un plazo de {dias_plazo} días.")
