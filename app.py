import streamlit as st
from supabase import create_client, Client
import re
import validadores as vl

# Configuración de conexión a Supabase
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("Sistema de Gestión - Turnos de Caja")

# Organización mediante pestañas ampliadas
pestana_registro, pestana_gestion, pestana_turnos, pestana_asignacion = st.tabs([
    "📝 Registrar Trabajador", 
    "👥 Gestión de Personal", 
    "⏰ Definir Turnos", 
    "📅 Asignación y Asistencia"
])

# -------------------------------------------------------------
# 1. PESTAÑA: REGISTRAR TRABAJADOR
# -------------------------------------------------------------
with pestana_registro:
    st.subheader("Ingreso de Nuevo Personal")
    with st.form("registro_form", clear_on_submit=True):
        nombres = st.text_input("Nombres")
        
        col1, col2 = st.columns(2)
        with col1:
            ape_paterno = st.text_input("Apellido Paterno")
        with col2:
            ape_materno = st.text_input("Apellido Materno")
            
        col3, col4 = st.columns([3, 1])
        with col3:
            rut_input = st.text_input(
                "RUT (Solo números, sin puntos ni DV)", 
                max_chars=8,
                placeholder="Ej: 12345678"
            )
        with col4:
            dv = st.text_input("DV", max_chars=1).upper()
            
        st.text("Celular (+56 9)")
        celular_input = st.text_input("Número de celular (8 dígitos)", max_chars=8, placeholder="12345678")
        
        disponibilidad = st.selectbox(
            "Disponibilidad",
            ["Semana", "Fin de semana", "Ambos"]
        )
        
        submit = st.form_submit_button("Guardar Registro")
        
        if submit:
            if not nombres or not ape_paterno or not ape_materno or not rut_input or not dv or not celular_input:
                st.warning("⚠️ Por favor, completa todos los campos.")
            elif not re.match("^[a-zA-ZÁÉÍÓÚáéíóúñÑ ]+$", nombres) or \
                 not re.match("^[a-zA-ZÁÉÍÓÚáéíóúñÑ ]+$", ape_paterno) or \
                 not re.match("^[a-zA-ZÁÉÍÓÚáéíóúñÑ ]+$", ape_materno):
                st.error("❌ Los nombres y apellidos solo deben contener letras.")
            elif not rut_input.isdigit() or len(rut_input) < 7 or len(rut_input) > 8:
                st.error("❌ El RUT debe contener entre 7 y 8 dígitos.")
            elif not celular_input.isdigit() or len(celular_input) != 8:
                st.error("❌ El celular debe contener exactamente 8 dígitos.")
            elif not vl.validar_rut_chileno(rut_input, dv):
                st.error("❌ El dígito verificador del RUT no es válido.")
            else:
                try:
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
                    supabase.table("Trabajador").insert(nuevo_trabajador).execute()
                    st.success(f"✅ ¡{nombres} registrado correctamente!")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")

# -------------------------------------------------------------
# 2. PESTAÑA: GESTIÓN DE PERSONAL
# -------------------------------------------------------------
with pestana_gestion:
    st.subheader("Lista y Eliminación de Personal")
    try:
        response = supabase.table("Trabajador").select("*").execute()
        trabajadores = response.data
        
        if trabajadores:
            st.dataframe(trabajadores, use_container_width=True)
            
            st.divider()
            st.write("### 🗑️ Eliminar Trabajador")
            opciones_eliminar = {f"{t['Nombre']} {t['Ape_Paterno']} (RUT: {t['rut']}-{t['dv']})": t['rut'] for t in trabajadores}
            trabajador_seleccionado = st.selectbox("Selecciona al trabajador a eliminar:", list(opciones_eliminar.keys()), key="del_trabajador")
            
            if st.button("Eliminar Registro", type="primary"):
                rut_a_borrar = opciones_eliminar[trabajador_seleccionado]
                try:
                    supabase.table("Trabajador").delete().eq("rut", rut_a_borrar).execute()
                    st.success(f"🗑️ Trabajador con RUT {rut_a_borrar} eliminado exitosamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ No se pudo eliminar: {e}")
        else:
            st.info("Aún no hay trabajadores registrados.")
    except Exception as e:
        st.error(f"❌ Error al cargar los datos: {e}")

# -------------------------------------------------------------
# 3. PESTAÑA: DEFINIR TURNOS
# -------------------------------------------------------------
with pestana_turnos:
    st.subheader("Crear Bloques de Turnos con Cupo Límite")
    
    with st.form("turno_form", clear_on_submit=True):
        nombre_turno = st.text_input("Nombre del Turno (Ej: Mañana, Tarde)")
        
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            hora_inicio = st.time_input("Hora de Inicio")
        with col_h2:
            hora_fin = st.time_input("Hora de Término")
        with col_h3:
            cupo_maximo = st.number_input("Cupo Máximo", min_value=1, max_value=50, value=5, step=1)
            
        submit_turno = st.form_submit_button("Guardar Turno")
        
        if submit_turno:
            if not nombre_turno:
                st.warning("⚠️ Debes asignar un nombre al turno.")
            else:
                try:
                    nuevo_turno = {
                        "nombre": nombre_turno,
                        "hora_inicio": str(hora_inicio),
                        "hora_fin": str(hora_fin),
                        "cupo_maximo": int(cupo_maximo)
                    }
                    supabase.table("Turno").insert(nuevo_turno).execute()
                    st.success(f"✅ Turno '{nombre_turno}' creado con un cupo máximo de {cupo_maximo} personas.")
                except Exception as e:
                    st.error(f"❌ Error al guardar el turno: {e}")
                    
    st.divider()
    st.write("### 📋 Turnos Registrados Actualmente")
    try:
        res_turnos = supabase.table("Turno").select("*").execute()
        if res_turnos.data:
            st.dataframe(res_turnos.data, use_container_width=True)
        else:
            st.info("No hay turnos configurados todavía.")
    except Exception as e:
        st.error(f"Error al listar turnos: {e}")

# -------------------------------------------------------------
# 4. PESTAÑA: ASIGNACIÓN Y ASISTENCIA
# -------------------------------------------------------------
with pestana_asignacion:
    st.subheader("Asignar Turnos y Controlar Cupos")
    
    try:
        res_t = supabase.table("Trabajador").select("rut, Nombre, Ape_Paterno").execute()
        res_turnos = supabase.table("Turno").select("id, nombre, hora_inicio, hora_fin, cupo_maximo").execute()
        
        trabajadores_list = res_t.data
        turnos_list = res_turnos.data
        
        if not trabajadores_list or not turnos_list:
            st.warning("⚠️ Debes tener al menos un trabajador registrado y un turno creado para poder hacer asignaciones.")
        else:
            with st.form("asignacion_form", clear_on_submit=True):
                dict_trabajadores = {f"{t['Nombre']} {t['Ape_Paterno']} (RUT: {t['rut']})": t['rut'] for t in trabajadores_list}
                trabajador_elegido = st.selectbox("Seleccionar Trabajador", list(dict_trabajadores.keys()))
                
                dict_turnos = {f"{tu['nombre']} ({tu['hora_inicio']} - {tu['hora_fin']}) [Máx: {tu['cupo_maximo']}]": tu for tu in turnos_list}
                turno_elegido_key = st.selectbox("Seleccionar Turno", list(dict_turnos.keys()))
                
                fecha_turno = st.date_input("Fecha del Turno")
                
                submit_asig = st.form_submit_button("Asignar Turno")
                
                if submit_asig:
                    rut_val = dict_trabajadores[trabajador_elegido]
                    turno_info = dict_turnos[turno_elegido_key]
                    id_turno_val = turno_info['id']
                    limite_cupo = turno_info['cupo_maximo']
                    
                    res_cuenta = supabase.table("Asignacion").select("id", count="exact").eq("turno_id", id_turno_val).eq("fecha", str(fecha_turno)).execute()
                    cupos_ocupados = res_cuenta.count if res_cuenta.count is not None else len(res_cuenta.data)
                    
                    if cupos_ocupados >= limite_cupo:
                        st.error(f"❌ No se puede asignar. Este turno ya alcanzó su cupo máximo de {limite_cupo} personas para el {fecha_turno}.")
                    else:
                        nueva_asignacion = {
                            "rut_trabajador": rut_val,
                            "turno_id": id_turno_val,
                            "fecha": str(fecha_turno),
                            "cumplido": False
                        }
                        supabase.table("Asignacion").insert(nueva_asignacion).execute()
                        st.success(f"✅ ¡Turno asignado exitosamente! (Cupos ocupados: {cupos_ocupados + 1}/{limite_cupo})")
            
            st.divider()
            st.subheader("✔️ Control de Cumplimiento y Asistencia")
            
            res_asig = supabase.table("Asignacion").select("*").execute()
            asignaciones = res_asig.data
            
            if asignaciones:
                st.write("Marca la casilla si el trabajador asistió y cumplió con su turno:")
                
                for asig in asignaciones:
                    t_info = next((t for t in trabajadores_list if t['rut'] == asig['rut_trabajador']), None)
                    tu_info = next((tu for tu in turnos_list if tu['id'] == asig['turno_id']), None)
                    
                    nombre_completo = f"{t_info['Nombre']} {t_info['Ape_Paterno']}" if t_info else "Desconocido"
                    nombre_turno = tu_info['nombre'] if tu_info else "Turno desconocido"
                    
                    col_info, col_check = st.columns([3, 1])
                    with col_info:
                        st.text(f"📅 Fecha: {asig['fecha']} | 👤 {nombre_completo} | ⏰ {nombre_turno}")
                    with col_check:
                        estado_actual = asig['cumplido']
                        nuevo_estado = st.checkbox("¿Cumplió?", value=estado_actual, key=f"check_{asig['id']}")
                        
                        if nuevo_estado != estado_actual:
                            supabase.table("Asignacion").update({"cumplido": nuevo_estado}).eq("id", asig['id']).execute()
                            st.rerun()
            else:
                st.info("No hay turnos asignados todavía.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar los módulos de asignación: {e}")