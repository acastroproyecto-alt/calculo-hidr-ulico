import streamlit as st
import numpy as np

# Configuración de página
st.set_page_config(page_title="Ingeniería Hidráulica - RNE", page_icon="💧", layout="wide")
st.title("💧 Sistema de Cálculo Hidráulico Sanitario (RNE)")
st.markdown("Transformación digital de memorias de cálculo para sistemas de agua potable.")

# --- BASE DE DATOS DE TABLAS RNE (Anexo 05) ---
TABLA_HUNTER = {
    3: 0.12, 4: 0.16, 5: 0.23, 6: 0.25, 7: 0.28, 8: 0.29, 9: 0.32, 10: 0.33,
    11: 0.355, 12: 0.38, 13: 0.40, 14: 0.42, 15: 0.44, 20: 0.54, 22: 0.58,
    27: 0.69, 52: 1.998, 62: 2.134, 72: 1.38, 115: 2.66, 118: 2.69, 138: 2.84, 157: 2.116
}

DIAMETROS_INTERIORES = {
    "PVC C-10": {0.5: 17.4, 0.75: 22.9, 1.0: 29.4, 1.25: 38.0, 1.5: 43.4, 2.0: 54.2},
    "PR-RCT PN 12.5": {0.5: 15.4, 0.75: 19.4, 1.0: 24.8, 1.25: 31.0, 1.5: 38.8, 2.0: 48.8},
    "PR-RCT PN 16": {0.5: 14.4, 0.75: 18.0, 1.0: 23.2, 1.25: 29.0, 1.5: 36.0, 2.0: 45.8}
}

ACCESORIOS_L_EQ = {
    0.5: {"codo": 0.532, "tee": 1.064, "check": 1.477, "compuerta": 0.112, "canastilla": 3.599, "flotador": 5.0},
    0.75: {"codo": 0.777, "tee": 1.554, "check": 2.159, "compuerta": 0.164, "canastilla": 5.260, "flotador": 5.0},
    1.0: {"codo": 1.023, "tee": 2.045, "check": 2.841, "compuerta": 0.216, "canastilla": 6.920, "flotador": 5.0},
    1.5: {"codo": 1.554, "tee": 3.109, "check": 4.318, "compuerta": 0.328, "canastilla": 10.519, "flotador": 5.0},
    2.0: {"codo": 2.045, "tee": 4.091, "check": 5.682, "compuerta": 0.432, "canastilla": 13.841, "flotador": 5.0}
}

def obtener_q_hunter(uh):
    if uh in TABLA_HUNTER:
        return TABLA_HUNTER[uh]
    # Interpolación simple aproximada si no se encuentra exacta
    uhs = sorted(TABLA_HUNTER.keys())
    if uh < uhs[0]: return TABLA_HUNTER[uhs[0]]
    if uh > uhs[-1]: return TABLA_HUNTER[uhs[-1]]
    for i in range(len(uhs)-1):
        if uhs[i] <= uh <= uhs[i+1]:
            x1, x2 = uhs[i], uhs[i+1]
            y1, y2 = TABLA_HUNTER[x1], TABLA_HUNTER[x2]
            return y1 + (uh - x1) * (y2 - y1) / (x2 - x1)
    return 0.40

# --- INTERFAZ EN PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "💧 1. Dotación y Almacenamiento", 
    "🎛️ 2. Carga y Medidor", 
    "📈 3. Unidades Hunter (MDS)", 
    "🚀 4. Sistema de Bombeo"
])

# === PESTAÑA 1: DOTACIÓN Y ALMACENAMIENTO ===
with tab1:
    st.header("Cálculo de Dotación Diaria y Volúmenes")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Datos de la Edificación")
        num_dormitorios = st.number_input("Cantidad de Dormitorios", min_value=1, value=6)
        dot_dorm = st.number_input("Dotación por persona/dormitorio (L/p/día)", value=155)
        area_estac = st.number_input("Área de Estacionamiento (m²)", value=13.43)
        dot_estac = st.number_input("Dotación Estacionamiento (L/m²/día)", value=2)

        total_lpd = (num_dormitorios * dot_dorm) + (area_estac * dot_estac)
        total_m3 = total_lpd / 1000
        
        st.metric(label="Total Dotación Diaria", value=f"{total_lpd:,.2f} L/día", delta=f"{total_m3:.4f} m³/día")

    with col2:
        st.subheader("Dimensionamiento de Cisterna")
        vol_proyectado = st.number_input("Volumen de Diseño Proyectado (m³)", value=4.0, step=0.5)
        largo = st.number_input("Largo de la cisterna (m)", value=2.0)
        ancho = st.number_input("Ancho de la cisterna (m)", value=1.5)
        altura_util = vol_proyectado / (largo * ancho)
        
        st.info(f"📐 Altura útil requerida calculada: **{altura_util:.2f} m**")
        altura_libre = st.number_input("Altura Libre de seguridad (m)", value=0.35)
        st.success(f"📏 Altura Total de la Cisterna: **{altura_util + altura_libre:.2f} m**")

# === PESTAÑA 2: CARGA DISPONIBLE EN MEDIDOR ===
with tab2:
    st.header("Cálculo de la Carga Disponible y Medidor")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Presiones y Condiciones de Red")
        pr_psi = st.number_input("Presión mínima red pública (psi)", value=20.0)
        pr_mca = pr_psi * 0.7032  # Conversión aproximada usada en tu excel
        st.caption(f"Equivalente a {pr_mca:.2f} mca")
        
        ps_mca = st.number_input("Presión mínima de salida a Cisterna (mca)", value=2.0)
        he_m = st.number_input("Nivel de ingreso respecto a red pública (m)", value=-1.0)
        t_llenado = st.number_input("Tiempo de llenado asumido (horas)", value=12.0)

        # Carga disponible Hf = Pr + He - Ps
        hf_mca = pr_mca + he_m - ps_mca
        st.metric(label="Carga Disponible Total (Hf)", value=f"{hf_mca:.2f} mca")

    with col2:
        st.subheader("Caudal de Entrada y Diámetro del Medidor")
        # Qc = Vc / Tc
        qc_m3h = vol_proyectado / t_llenado
        qc_lps = (qc_m3h * 1000) / 3600
        
        st.write(f"**Caudal requerido (Qc):** {qc_lps:.4f} lt/seg | {qc_m3h:.4f} m³/h")
        
        hm_max = hf_mca * 0.50
        st.warning(f"La pérdida máx. admisible en el medidor (50% Hf) es: {hm_max:.2f} mca")
        
        diam_comercial = st.selectbox("Diámetro comercial seleccionado para Medidor (pulg)", [0.5, 0.75, 1.0])
        hm_abaco = st.number_input("Pérdida real del medidor según ábaco (mca)", value=0.12)
        
        if hm_abaco <= hm_max:
            st.success("✅ ¡CUMPLE! La pérdida real del medidor es menor al límite admisible.")
        else:
            st.error("❌ ¡ALERTA! El diámetro seleccionado genera demasiada pérdida.")

# === PESTAÑA 3: MÁXIMA DEMANDA SIMULTÁNEA ===
with tab3:
    st.header("Cálculo de Gastos Probables (Unidades Hunter)")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Configuración de Aparatos Sanitarios")
        # Formulario rápido para simular la tabla de aparatos
        u_publico = st.checkbox("¿Uso Público?", value=True)
        tipo_u = "U.T." if u_publico else "U.C."
        
        cant_inodoros = st.number_input("Inodoros con Tanque", min_value=0, value=2)
        cant_lavatorios = st.number_input("Lavatorios", min_value=0, value=3)
        cant_lavaderos = st.number_input("Lavaderos de Cocina/Ropa", min_value=0, value=2)
        
        # Pesos Hunter típicos simplificados según tus datos
        peso_inodoro = 5 if u_publico else 3
        peso_lavatorio = 2 if u_publico else 1
        peso_lavadero = 3 if u_publico else 2
        
        total_uh = (cant_inodoros * peso_inodoro) + (cant_lavatorios * peso_lavatorio) + (cant_lavaderos * peso_lavadero)
        
    with col2:
        st.subheader("Caudal de Diseño")
        st.metric(label="Total Unidades Hunter (UH)", value=int(total_uh))
        
        q_diseno = obtener_q_hunter(int(total_uh))
        st.metric(label="Caudal Probable (Q)", value=f"{q_diseno:.2f} L/s")
        st.info(f"Método RNE aplicado para tipo de unidades: {tipo_u}")

# === PESTAÑA 4: SISTEMA DE BOMBEO ===
with tab4:
    st.header("Cálculo de Sistema de Bombeo y Altura Dinámica")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Datos de la Línea")
        mat_tub = st.selectbox("Material de la Tubería", ["PVC", "PR-RCT PN 12.5", "PR-RCT PN 16"])
        c_hazen = 140 if "PVC" in mat_tub or "PR" in mat_tub else 120
        
        d_pulg = st.selectbox("Diámetro Comercial de Impulsión (pulg)", [0.5, 0.75, 1.0, 1.25, 1.5, 2.0], index=3)
        d_int_mm = DIAMETROS_INTERIORES[mat_tub][d_pulg]
        d_int_m = d_int_mm / 1000
        
        long_tub = st.number_input("Longitud física de tubería (m)", value=10.0)
        
        # Accesorios
        st.caption("Cantidad de Accesorios en la ruta crítica")
        codos = st.number_input("Codos de 90°", value=3)
        tees = st.number_input("Tees", value=1)
        valv_chk = st.number_input("Válvulas Check", value=1)
        
        # Longitud equivalente
        l_eq_total = (codos * ACCESORIOS_L_EQ[d_pulg]["codo"] + 
                      tees * ACCESORIOS_L_EQ[d_pulg]["tee"] + 
                      valv_chk * ACCESORIOS_L_EQ[d_pulg]["check"])
        long_total = long_tub + l_eq_total
        
    with col2:
        st.subheader("Resultados Hidráulicos del Bombeo")
        hg = st.number_input("Altura Geométrica de elevación (m)", value=6.33)
        ps_final = st.number_input("Presión de entrega requerida en punto crítico (mca)", value=2.0)
        
        # Caudal en m3/s para Hazen-Williams
        q_m3s = q_diseno / 1000
        velocidad = q_m3s / (np.pi * (d_int_m**2) / 4)
        
        st.write(f"**Velocidad en tubería:** {velocidad:.2f} m/s")
        if velocidad > 2.0:
            st.error("❌ La velocidad supera los 2.0 m/s máximos permitidos por el RNE.")
        else:
            st.success("✅ Velocidad dentro del rango reglamentario.")
            
        # Pérdida de carga por Hazen-Williams
        hf_friccion = 10.674 * (q_m3s**1.852) / (c_hazen**1.852 * d_int_m**4.87) * long_total
        hdt = hg + hf_friccion + ps_final
        
        st.metric(label="Altura Dinámica Total (HDT)", value=f"{hdt:.2f} m")
        
        # Potencia Eléctrica / Comercial
        eficiencia_bomba = st.slider("Eficiencia de la Bomba (%)", 40, 80, 60) / 100
        potencia_hp = (q_diseno * hdt) / (75 * eficiencia_bomba * 0.746) # Conversión a HP métrico/eléctrico aprox
        
        st.metric(label="Potencia Teórica del Motor", value=f"{potencia_hp:.3f} HP")
        
        pot_comercial = 0.5 if potencia_hp <= 0.5 else (0.75 if potencia_hp <= 0.75 else 1.0)
        st.success(f"⚡ **Potencia Comercial Recomendada:** {pot_comercial} HP")
