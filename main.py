"""Aplicación principal - Informe Mensual de Backup.

Sistema para procesamiento y visualización de reportes de backup
de Data Protector Cell Managers. Interfaz web con Streamlit.
"""

import streamlit as st
import pandas as pd
import os
import sys
import tempfile
import time
import shutil
import uuid
from datetime import datetime, date, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers.csv_parser import parse_csv_file, parse_multiple_csvs
from parsers.schedule_parser import parse_schedule_file
from models.report_data import CellManagerReport, ScheduleReport
from utils.calculations import format_pct, format_tb, get_compliance_color, get_kpi_color

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

CELL_MANAGERS = ["COMHP81", "COMHP83", "LNXCELLMNGVEN", "LNXCELLMNGPTA", "LNXCELLMNGTRI"]

# ── SESSION STATE INITIALIZATION ──
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Directorio temporal único por sesión para aislamiento
BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "streamlit_backup_uploads")
SESSION_TEMP_DIR = os.path.join(BASE_TEMP_DIR, st.session_state.session_id)
os.makedirs(SESSION_TEMP_DIR, exist_ok=True)

# Colores
ACCENT = "#58a6ff"
SUCCESS = "#3fb950"
WARNING = "#d29922"
ERROR_ = "#f85149"

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Informe Mensual Backup - Data Protector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS Custom (Dark Default)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #e6edf3; }

    /* Header */
    .main-header {
        display: flex; align-items: center; gap: 16px;
        padding: 8px 0 16px 0; border-bottom: 1px solid #30363d; margin-bottom: 24px;
    }
    .header-icon {
        background: #1f6feb30; border-radius: 12px; padding: 12px;
        display: flex; align-items: center; justify-content: center; font-size: 24px;
    }
    .header-title { font-size: 20px; font-weight: 700; color: #e6edf3; }
    .header-sub { font-size: 12px; color: #8b949e; }

    /* Cards */
    .kpi-card, .upload-card, .totals-row, .progress-tracker {
        background: #1c2128; border: 1px solid #30363d; border-radius: 6px; padding: 16px;
    }
    .upload-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
    .cm-icon { background: #1f6feb25; border-radius: 6px; padding: 8px; font-size: 18px; }
    .cm-name { font-size: 14px; font-weight: 600; color: #e6edf3; }
    .cm-sub { font-size: 11px; color: #8b949e; }

    /* Totals */
    .total-item { text-align: center; min-width: 100px; position: relative; cursor: help; }
    .total-icon { font-size: 18px; margin-bottom: 2px; }
    .total-label { font-size: 10px; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
    .total-value { font-size: 20px; font-weight: 700; color: #58a6ff; }

    /* KPIs */
    .kpi-label { font-size: 11px; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 28px; font-weight: 700; margin: 4px 0; }
    .kpi-bar { height: 6px; border-radius: 3px; background: #21262d; margin-top: 8px; overflow: hidden; }
    .kpi-fill { height: 100%; border-radius: 3px; }

    /* Tooltips */
    .tip { position: relative; cursor: help; }
    .tip .tip-text {
        visibility: hidden; opacity: 0; position: absolute; bottom: 110%; left: 50%; transform: translateX(-50%);
        background: #1c2128; color: #e6edf3; border: 1px solid #30363d; border-radius: 6px;
        padding: 8px 12px; font-size: 11px; white-space: nowrap; z-index: 100;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4); text-transform: none; letter-spacing: 0;
    }
    .tip:hover .tip-text { visibility: visible; opacity: 1; }

    /* Metric overrides */
    div[data-testid="stMetric"], [data-testid="stDataFrame"] {
        background-color: #1c2128; border: 1px solid #30363d !important;
        border-radius: 6px !important; box-shadow: none !important;
    }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    
    /* Progress Tracker Styles */
    .progress-items { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .progress-item { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }
    .item-done { background: #23863640; color: #3fb950; }
    .item-pending { background: #30363d; color: #8b949e; }
    
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Login Style - Centered Card Approach */
    [data-testid="stForm"] {
        background-color: #1c2128;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 40px;
        max-width: 400px;
        margin: 10vh auto; /* Center vertically and horizontally */
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    }
    .login-icon {
        width: 60px; height: 60px; margin: 0 auto 16px;
        background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%);
        border-radius: 14px; display: flex; align-items: center; justify-content: center;
        font-size: 28px;
    }
    .login-title { font-size: 20px; font-weight: 700; color: #e6edf3; margin-bottom: 6px; text-align: center; }
    .login-sub { font-size: 13px; color: #8b949e; margin-bottom: 32px; text-align: center; }
    
    /* Input Styling to match dark theme explicitly */
    div[data-baseweb="input"] { background-color: #0d1117 !important; border: 1px solid #30363d !important; color: white !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

def check_credentials(username: str, password: str) -> bool:
    """Valida credenciales contra st.secrets."""
    try:
        valid_user = st.secrets["auth"]["username"]
        valid_pass = st.secrets["auth"]["password"]
        return username == valid_user and password == valid_pass
    except Exception:
        return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Contenedor principal que centra todo verticalmente si es necesario (el margen auto del CSS hace el resto)
    with st.form("login_form"):
        st.markdown("""
            <div class="login-icon">🛡️</div>
            <div class="login-title">Backup Dashboard</div>
            <div class="login-sub">Acceso Seguro</div>
        """, unsafe_allow_html=True)

        username = st.text_input("Usuario", placeholder="Usuario", label_visibility="collapsed")
        password = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submit:
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()


# ══════════════════════════════════════════════════════════════
# DATA FILTERING HELPERS
# ══════════════════════════════════════════════════════════════

def filter_cm_report(report: CellManagerReport, start_date: date, end_date: date) -> CellManagerReport:
    """Filtra las sesiones de un reporte por rango de fechas y recalcula métricas."""
    filtered_sessions = []
    unique_specs = set()
    total_gb = 0.0
    successful_jobs = 0

    end_datetime = datetime.combine(end_date, datetime.max.time())
    start_datetime = datetime.combine(start_date, datetime.min.time())

    for s in report.sessions:
        if s.start_datetime:
            # s.start_datetime es datetime
            if start_datetime <= s.start_datetime <= end_datetime:
                filtered_sessions.append(s)
                unique_specs.add(s.specification)
                total_gb += s.gb_written
                if s.success and s.success.strip() != "0%":
                    successful_jobs += 1
    
    total_jobs = len(filtered_sessions)
    compliance = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0

    return CellManagerReport(
        cell_manager=report.cell_manager,
        total_policies=len(unique_specs),
        total_jobs=total_jobs,
        size_tb=round(total_gb / 1024, 2),
        compliance_pct=round(compliance, 2),
        sessions=filtered_sessions
    )

def get_date_range(data):
    """Obtiene min y max date de todos los datos cargados."""
    min_d = None
    max_d = None
    for rep in data.values():
        for s in rep.sessions:
            if s.start_datetime:
                d = s.start_datetime.date()
                if min_d is None or d < min_d: min_d = d
                if max_d is None or d > max_d: max_d = d
    return min_d, max_d


# ══════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ══════════════════════════════════════════════════════════════

if "cell_manager_data" not in st.session_state:
    st.session_state.cell_manager_data = {}
if "cell_manager_files" not in st.session_state:
    st.session_state.cell_manager_files = {cm: [] for cm in CELL_MANAGERS}
if "schedule_report" not in st.session_state:
    st.session_state.schedule_report = None
if "schedule_file_name" not in st.session_state:
    st.session_state.schedule_file_name = ""

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════

filtered_cm_data = st.session_state.cell_manager_data  # Default: sin filtrar

with st.sidebar:
    _, col_title, _ = st.columns([1, 8, 1])
    with col_title:
        st.markdown("### 🛡️ Backup Dashboard")
    st.markdown("---")



    page = st.radio("MENÚ", ["📂 Carga de Archivos", "📊 Métricas"], label_visibility="collapsed")
    st.markdown("---")

    # FILTRO DE FECHAS
    if st.session_state.cell_manager_data:
        min_date, max_date = get_date_range(st.session_state.cell_manager_data)
        if min_date and max_date:
            st.markdown("**FILTROS**")
            try:
                # Default: últimos 30 días o rango completo si es menor
                default_start = max_date - timedelta(days=30)
                if default_start < min_date: default_start = min_date
                
                date_range = st.date_input(
                    "Rango de Fechas",
                    value=(default_start, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_d, end_d = date_range
                    # Aplicar filtro
                    new_data = {}
                    for cm_name, rep in st.session_state.cell_manager_data.items():
                        new_data[cm_name] = filter_cm_report(rep, start_d, end_d)
                    filtered_cm_data = new_data
                    st.caption(f"Mostrando: {start_d} a {end_d}")
            except Exception as e:
                st.error(f"Error en filtro: {e}")
            st.markdown("---")


    # Estado de Carga Compacto
    st.markdown("**ESTADO DE CARGA**")
    
    # Barra de Progreso Minimalista
    cm_loaded = len(st.session_state.cell_manager_data)
    has_sched = st.session_state.schedule_report is not None
    total_steps = len(CELL_MANAGERS) + 1
    done_steps = cm_loaded + (1 if has_sched else 0)
    
    if done_steps < total_steps:
        st.progress(done_steps / total_steps)
        st.caption(f"Progreso: {done_steps}/{total_steps}")
    else:
        st.success("Carga Completa")

    st.markdown("---")
    
    # Lista Compacta de Items
    for cm in CELL_MANAGERS:
        loaded = cm in st.session_state.cell_manager_data
        if loaded:
            st.markdown(f"🟢 **{cm}**")
        else:
            st.markdown(f"⚪ {cm}")

    if has_sched:
        st.markdown(f"🟢 **Schedule**")
    else:
        st.markdown(f"⚪ Schedule")

    # ── ACCIONES (Parte inferior del sidebar) ──
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # BOTÓN DE LIMPIEZA
    if st.button("🗑️ Limpiar Datos", type="secondary", use_container_width=True):
        st.session_state.confirm_clear = True
    
    if st.session_state.get("confirm_clear", False):
        st.warning("¿Borrar todos los datos y archivos cargados?", icon="⚠️")
        col_yes, col_no = st.columns(2)
        if col_yes.button("Sí, borrar", type="primary", use_container_width=True):
            try:
                if os.path.exists(SESSION_TEMP_DIR):
                    shutil.rmtree(SESSION_TEMP_DIR)
                os.makedirs(SESSION_TEMP_DIR, exist_ok=True)
            except Exception as e:
                print(f"Error limpiando temp: {e}")
            # 2. Resetear variables de datos (MANTENIENDO SESIÓN)
            keys_to_reset = ["cell_manager_data", "cell_manager_files", "schedule_report", "schedule_file_name"]
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.confirm_clear = False
            # Asegurar que la sesión no se pierda
            st.session_state.authenticated = True
            st.success("¡Datos limpiados exitosamente!")
            time.sleep(0.5)
            st.rerun()
        if col_no.button("Cancelar", use_container_width=True):
            st.session_state.confirm_clear = False
            st.rerun()

    # BOTÓN LOGOUT
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        # Limpieza física al salir
        try:
            if os.path.exists(SESSION_TEMP_DIR):
                shutil.rmtree(SESSION_TEMP_DIR)
        except Exception:
            pass
        st.session_state.clear()
        st.rerun()


def save_temp_file(uploaded_file) -> str:
    """Guarda UploadedFile en temp de la sesión y retorna path."""
    file_path = os.path.join(SESSION_TEMP_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def process_cm_files(cm_name: str, files) -> CellManagerReport:
    """Procesa archivos CSV de un Cell Manager con barra de progreso."""
    bar = st.progress(0, text=f"Procesando {cm_name}...")
    paths = []

    for i, f in enumerate(files):
        bar.progress((i + 1) / (len(files) + 1), text=f"Guardando {f.name}...")
        paths.append(save_temp_file(f))

    bar.progress(0.9, text=f"Parseando {len(paths)} archivos...")
    report = parse_multiple_csvs(paths, cm_name)

    bar.progress(1.0, text=f"✅ {cm_name}: {report.total_jobs} jobs procesados")
    time.sleep(0.3)
    bar.empty()

    return report, paths


def process_schedule(file) -> ScheduleReport:
    """Procesa el Schedule Excel con barra de progreso."""
    bar = st.progress(0, text="Guardando archivo...")
    path = save_temp_file(file)

    bar.progress(0.5, text=f"Parseando {file.name}...")
    period = file.name.replace(".xlsx", "").replace(".xlsm", "")
    report = parse_schedule_file(path, period)

    bar.progress(1.0, text=f"✅ Schedule cargado: {period}")
    time.sleep(0.3)
    bar.empty()

    return report


# ══════════════════════════════════════════════════════════════
# VISTA: CARGA DE ARCHIVOS
# ══════════════════════════════════════════════════════════════

if page == "📂 Carga de Archivos":
    st.markdown("""
    <div class="main-header">
        <div class="header-icon">📂</div>
        <div>
            <div class="header-title">Carga de Archivos</div>
            <div class="header-sub">Selecciona los reportes CSV de cada Cell Manager y el Schedule mensual.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PROGRESS TRACKER GENERAL ──
    cm_loaded = len(st.session_state.cell_manager_data)
    has_sched = st.session_state.schedule_report is not None
    total_steps = len(CELL_MANAGERS) + 1
    done_steps = cm_loaded + (1 if has_sched else 0)
    pct = int(done_steps / total_steps * 100)
    color = SUCCESS if pct == 100 else (WARNING if pct > 0 else "#484f58")

    items_html = ""
    for cm in CELL_MANAGERS:
        loaded = cm in st.session_state.cell_manager_data
        cls = "item-done" if loaded else "item-pending"
        icon = "✓" if loaded else "○"
        extra = ""
        if loaded:
            r = st.session_state.cell_manager_data[cm]
            extra = f" · {r.total_jobs} jobs"
        items_html += f'<span class="progress-item {cls}">{icon} {cm}{extra}</span>'

    sched_cls = "item-done" if has_sched else "item-pending"
    sched_icon = "✓" if has_sched else "○"
    sched_extra = f" · {st.session_state.schedule_report.period_name}" if has_sched else ""
    items_html += f'<span class="progress-item {sched_cls}">{sched_icon} Schedule{sched_extra}</span>'

    st.markdown(f"""
    <div class="progress-tracker">
        <div class="progress-title">📊 Progreso de Carga</div>
        <div style="display:flex; align-items:baseline; gap:4px;">
            <span class="progress-pct" style="color:{color}">{pct}%</span>
            <span class="progress-detail">{done_steps} de {total_steps} completados</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:{pct}%; background:{color}"></div>
        </div>
        <div class="progress-items">{items_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── CELL MANAGERS ──
    st.markdown('<p style="font-size:11px; color:#484f58; font-weight:600; letter-spacing:1px; margin-bottom:4px;">CELL MANAGERS</p>', unsafe_allow_html=True)

    cols = st.columns(2)
    for i, cm in enumerate(CELL_MANAGERS):
        with cols[i % 2]:
            has_data = cm in st.session_state.cell_manager_data

            if has_data:
                report = st.session_state.cell_manager_data[cm]
                files_count = len(st.session_state.cell_manager_files[cm])
                status_html = f'<span class="progress-item item-done">✓ {files_count} archivos · {report.total_jobs} jobs · {format_tb(report.size_tb)}</span>'
            else:
                status_html = '<span class="progress-item item-pending">○ Sin archivos cargados</span>'

            st.markdown(f"""
            <div class="upload-card">
                <div class="upload-card-header">
                    <div class="cm-icon">🖥️</div>
                    <div>
                        <div class="cm-name">{cm}</div>
                        <div class="cm-sub">Cell Manager</div>
                    </div>
                </div>
                <hr style="border-color:#30363d; margin:8px 0;">
                {status_html}
            </div>
            """, unsafe_allow_html=True)

            csv_files = st.file_uploader(
                f"CSVs de {cm}",
                type=["csv"],
                accept_multiple_files=True,
                key=f"csv_{cm}",
                label_visibility="collapsed",
            )

            if csv_files and (not has_data or len(csv_files) != len(st.session_state.cell_manager_files.get(cm, []))):
                report, paths = process_cm_files(cm, csv_files)
                st.session_state.cell_manager_data[cm] = report
                st.session_state.cell_manager_files[cm] = paths
                st.rerun()

    # ── SCHEDULE ──
    st.markdown('<p style="font-size:11px; color:#484f58; font-weight:600; letter-spacing:1px; margin:24px 0 4px 0;">SCHEDULE MENSUAL</p>', unsafe_allow_html=True)

    has_schedule = st.session_state.schedule_report is not None

    if has_schedule:
        sched_status = f'<span class="progress-item item-done">✓ Periodo: {st.session_state.schedule_report.period_name}</span>'
        sched_sub = st.session_state.schedule_file_name
    else:
        sched_status = '<span class="progress-item item-pending">○ Sin archivo cargado</span>'
        sched_sub = "Archivo Excel de programación"

    st.markdown(f"""
    <div class="upload-card" style="max-width:480px; border-color:#d2992240;">
        <div class="upload-card-header">
            <div class="cm-icon" style="background:#d2992225;">📅</div>
            <div>
                <div class="cm-name">Schedule Mensual</div>
                <div class="cm-sub">{sched_sub}</div>
            </div>
        </div>
        <hr style="border-color:#30363d; margin:8px 0;">
        {sched_status}
    </div>
    """, unsafe_allow_html=True)

    schedule_file = st.file_uploader(
        "Schedule Excel",
        type=["xlsx", "xlsm"],
        key="schedule_upload",
        label_visibility="collapsed",
    )

    if schedule_file and not has_schedule:
        report = process_schedule(schedule_file)
        st.session_state.schedule_report = report
        st.session_state.schedule_file_name = schedule_file.name
        st.rerun()


# ══════════════════════════════════════════════════════════════
# VISTA: DASHBOARD
# ══════════════════════════════════════════════════════════════

elif page == "📊 Métricas":
    st.markdown("""
    <div class="main-header">
        <div class="header-icon">📊</div>
        <div>
            <div class="header-title">Métricas</div>
            <div class="header-sub">Informe Mensual · Backup & Recovery</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cell_manager_data = filtered_cm_data
    schedule_report = st.session_state.schedule_report

    # ── Sin datos ──
    if not cell_manager_data and not schedule_report:
        st.markdown("""
        <div style="text-align:center; padding:80px 0;">
            <div style="font-size:64px; margin-bottom:16px;">📊</div>
            <div style="font-size:16px; font-weight:500; color:#8b949e; margin-bottom:8px;">Sin datos para mostrar</div>
            <div style="font-size:13px; color:#484f58;">Carga archivos en la sección de <b>Carga de Archivos</b> para generar el dashboard.</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # RESUMEN POR CELL MANAGER
    # ══════════════════════════════════════════════════════

    if cell_manager_data:
        st.subheader("Resumen por Cell Manager")

        total_jobs = sum(r.total_jobs for r in cell_manager_data.values())
        total_policies = sum(r.total_policies for r in cell_manager_data.values())
        total_tb = sum(r.size_tb for r in cell_manager_data.values())
        avg_compliance = (
            sum(r.compliance_pct * r.total_jobs for r in cell_manager_data.values()) / total_jobs
            if total_jobs > 0 else 0
        )

        # Tarjetas individuales de totales
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💼 Total Jobs", f"{total_jobs:,}", help="Suma de todos los jobs de backup ejecutados en todos los Cell Managers.")
        c2.metric("📋 Políticas Únicas", str(total_policies), help="Cantidad de políticas de backup únicas configuradas en todos los Cell Managers.")
        c3.metric("💾 Size Total", format_tb(total_tb), help="Tamaño total en Terabytes de datos respaldados.")
        c4.metric("✅ Cumplimiento", format_pct(avg_compliance), help="Promedio ponderado: Σ(cumplimiento × jobs) / total_jobs")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Tabla detalle con fila TOTAL
        table_data = []
        for cm_name, report in cell_manager_data.items():
            table_data.append({
                "Plataforma": cm_name,
                "Cant. Políticas": report.total_policies,
                "Jobs": report.total_jobs,
                "Size TB": report.size_tb,
                "% Cumplimiento": report.compliance_pct,
            })
        table_data.append({
            "Plataforma": "⚡ TOTAL",
            "Cant. Políticas": total_policies,
            "Jobs": total_jobs,
            "Size TB": round(total_tb, 2),
            "% Cumplimiento": round(avg_compliance, 2),
        })

        df_cm = pd.DataFrame(table_data)
        st.dataframe(
            df_cm,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Plataforma": st.column_config.TextColumn("Plataforma", width="medium"),
                "Jobs": st.column_config.NumberColumn("Jobs", format="%d"),
                "Size TB": st.column_config.NumberColumn("Size TB", format="%.2f"),
                "% Cumplimiento": st.column_config.NumberColumn("% Cumplimiento", format="%.2f%%"),
            },
        )

    # ══════════════════════════════════════════════════════
    # SCHEDULE
    # ══════════════════════════════════════════════════════

    if schedule_report:
        st.markdown("---")
        st.subheader("Schedule Mensual")
        st.caption(f"Periodo: {schedule_report.period_name}")
        sr = schedule_report

        # KPIs con gauges
        k1, k2, k3 = st.columns(3)

        with k1:
            color_op = get_kpi_color(sr.kpi_operacion_general)
            st.markdown(f"""
            <div class="kpi-card tip">
                <div class="kpi-label">📈 KPI Operación</div>
                <div class="kpi-value" style="color:{color_op}">{format_pct(sr.kpi_operacion_general)}</div>
                <div class="kpi-bar"><div class="kpi-fill" style="width:{min(sr.kpi_operacion_general, 100)}%; background:{color_op}"></div></div>
                <div class="kpi-formula">(Programados − Fallidos) / Programados × 100</div>
                <span class="tip-text">Efectividad operacional: mide el % de jobs que no fallaron</span>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            color_gf = get_kpi_color(sr.kpi_gestion_fallidos_general)
            st.markdown(f"""
            <div class="kpi-card tip">
                <div class="kpi-label">🔧 KPI Gestión Fallidos</div>
                <div class="kpi-value" style="color:{color_gf}">{format_pct(sr.kpi_gestion_fallidos_general)}</div>
                <div class="kpi-bar"><div class="kpi-fill" style="width:{min(sr.kpi_gestion_fallidos_general, 100)}%; background:{color_gf}"></div></div>
                <div class="kpi-formula">Total Fallidos Gestionados / Total casos × 100</div>
                <span class="tip-text">Casos gestionados sobre el total de incidentes (Fallidos + Relanzados)</span>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            st.markdown(f"""
            <div class="kpi-card tip">
                <div class="kpi-label">🔄 % Relanzados</div>
                <div class="kpi-value" style="color:{WARNING}">{format_pct(sr.pct_relanzados_general)}</div>
                <div class="kpi-bar"><div class="kpi-fill" style="width:{min(sr.pct_relanzados_general, 100)}%; background:{WARNING}"></div></div>
                <div class="kpi-formula">Relanzados / (Programados − Fallidos) × 100</div>
                <span class="tip-text">Jobs con status 'Relaunched' o columna Relanzado / Exitosos</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Métricas de Volumen (5 columnas)
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("📅 Programados", f"{sr.total_programados:,}", help="Total de jobs programados en el periodo")
        s2.metric("▶️ Ejecutados", f"{sr.total_ejecutados:,}", help="Jobs completados exitosamente (cualquier estado completed)")
        s3.metric("❌ Fallidos", f"{sr.total_fallidos:,}", help="Jobs con estado 'Failed' o 'Aborted' (estricto)")
        s4.metric("🔄 Relanzados", f"{sr.total_relanzados:,}", help="Jobs con status 'Relaunched' o columna Relanzado / Exitosos")
        s5.metric("🎫 Casos ITSM", f"{sr.total_q:,}", help="Tickets ITSM creados (WO/RF/CHG/REQ/INC)")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Tabla Schedule con fila TOTAL
        st.markdown("##### 📅 Detalle Schedule")
        sched_data = []
        for row in sr.rows:
            sched_data.append({
                "Resumen": row.platform,
                "Ejecutados": row.ejecutados,
                "Programados": row.programados,
                "Relanzados": row.relanzados,
                "Fallidos": row.fallidos,
                "Casos ITSM": row.q,
                "Ind. Efect. Op.": row.kpi_operacion,
                "Relanzamiento": row.pct_relanzamiento,
                "Gest. Fallidos": row.gestion_fallidos,
            })
        sched_data.append({
            "Resumen": "⚡ TOTAL",
            "Ejecutados": sr.total_ejecutados,
            "Programados": sr.total_programados,
            "Relanzados": sr.total_relanzados,
            "Fallidos": sr.total_fallidos,
            "Casos ITSM": sr.total_q,
            "Ind. Efect. Op.": sr.kpi_operacion_general,
            "Relanzamiento": sr.pct_relanzados_general,
            "Gest. Fallidos": sr.kpi_gestion_fallidos_general,
        })

        df_sched = pd.DataFrame(sched_data)
        st.dataframe(
            df_sched,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ejecutados": st.column_config.NumberColumn(format="%d"),
                "Programados": st.column_config.NumberColumn(format="%d"),
                "Relanzados": st.column_config.NumberColumn(format="%d"),
                "Fallidos": st.column_config.NumberColumn(format="%d"),
                "Casos ITSM": st.column_config.NumberColumn(format="%d"),
                "Ind. Efect. Op.": st.column_config.NumberColumn(format="%.2f%%"),
                "Relanzamiento": st.column_config.NumberColumn(format="%.2f%%"),
                "Gest. Fallidos": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )


