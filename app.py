import streamlit as st
from supabase import create_client, Client
import re
import validadores as vl

# Conexión a Supabase usando tus secretos
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("Registro de Equipo - Turnos de Caja")

with st.form("registro_form", clear_on_submit=False):
    st.write("**Ingresa los datos del trabajador**")
    
    nombres = st.text_input("Nombres")
    
    col1, col2 = st.columns(2)
    with col1:
        ape_paterno = st.text_input("Apellido Paterno")
    with col2:
        ape_materno = st.text_input("Apellido Materno")
        
    col3, col4 = st.columns([3, 1])
    with col3:
        # Campo de texto limpio sin el contador molesto
        rut_input = st.text_input(
            "RUT (Solo números, sin puntos ni DV)", 
            max_chars=8,
            placeholder="Ej: 12345678"
        )
    with col4:
        dv = st.text_input("DV", max_chars=1).upper()
        
    # Celular adaptado con prefijo fijo de Chile
    st.text("Celular (+56 9)")
    celular_input = st.text_input("Número de celular (8 dígitos)", max_chars=8, placeholder="12345678")
    
    disponibilidad = st.selectbox(
        "Disponibilidad",
        ["Semana", "Fin de semana", "Ambos"]
    )
    
    submit = st.form_submit_button("Guardar Registro")
    
    if submit:
        # 1. Validar que no queden campos vacíos
        if not nombres or not ape_paterno or not ape_materno or not rut_input or not dv or not celular_input:
            st.warning("⚠️ Por favor, completa todos los campos.")
        
        # 2. Validar que nombres y apellidos solo tengan letras (sin números ni puntos)
        elif not re.match("^[a-zA-ZÁÉÍÓÚáéíóúñÑ ]+$", nombres) or \
             not re.match("^[a-zA-ZÁÉÍÓÚáéíóúñÑ ]+$", ape_paterno) or \
             not re.match("^[a-zA-ZÁÉÍÓÚáéíóúñÑ ]+$", ape_materno):
            st.error("❌ Los nombres y apellidos solo deben contener letras (sin números ni puntos).")
            
        # 3. Validar que el RUT sean solo números y tenga el largo correcto (7 u 8 dígitos)
        elif not rut_input.isdigit() or len(rut_input) < 7 or len(rut_input) > 8:
            st.error("❌ El RUT debe contener entre 7 y 8 dígitos (sin puntos ni dígito verificador).")
            
        # 4. Validar que el celular tenga exactamente 8 dígitos y sean puramente números
        elif not celular_input.isdigit() or len(celular_input) != 8:
            st.error("❌ El número de celular debe contener exactamente 8 dígitos (después del +56 9).")

        # 5. Validar que el RUT matemáticamente exista (Módulo 11)
        elif not vl.validar_rut_chileno(rut_input, dv):
            st.error("❌ El RUT ingresado no es válido (el dígito verificador no coincide).")    
        else:
            try:
                # Unimos el prefijo fijo con los 8 dígitos ingresados
                celular_completo = f"+569{celular_input}"
                
                nuevo_trabajador = {
                    "Nombre": nombres,
                    "Ape_Paterno": ape_paterno,
                    "Ape_Materno": ape_materno,
                    "rut": int(rut_input),
                    "dv": dv,
                    "celular": celular_completo,
                    "disponibilidad": disponibilidad
                }
                
                # Usamos "Trabajador" con T mayúscula tal como quedó en Supabase
                respuesta = supabase.table("Trabajador").insert(nuevo_trabajador).execute()
                st.success(f"✅ ¡{nombres} registrado correctamente en el sistema!")
                
            except Exception as e:
                st.error("❌ Error al guardar. Es posible que el RUT o el celular ya se encuentren registrados.")
st.divider()
st.subheader("Personal Registrado en el Sistema")

try:
    # Consultamos todos los registros de la tabla Trabajador
    response = supabase.table("Trabajador").select("*").execute()
    trabajadores = response.data
    
    if trabajadores:
        # Mostramos los datos en una tabla interactiva de Streamlit
        st.dataframe(trabajadores, use_container_width=True)
    else:
        st.info("Aún no hay trabajadores registrados en la base de datos.")
        
except Exception as e:
    st.error(f"❌ Error al cargar la lista de trabajadores: {e}")