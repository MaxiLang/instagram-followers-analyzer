"""
Instagram Followers Analyzer
Aplicación Streamlit profesional para analizar seguidores de Instagram
"""

import streamlit as st
import json
import pandas as pd
from io import BytesIO
from typing import Set, List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================

# Instagram SVG icon (base64 encoded for favicon)
INSTAGRAM_ICON = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 448 512'><defs><linearGradient id='ig' x1='0%25' y1='100%25' x2='100%25' y2='0%25'><stop offset='0%25' style='stop-color:%23FFDC80'/><stop offset='25%25' style='stop-color:%23FCAF45'/><stop offset='50%25' style='stop-color:%23F77737'/><stop offset='75%25' style='stop-color:%23F56040'/><stop offset='100%25' style='stop-color:%23C13584'/></linearGradient></defs><path fill='url(%23ig)' d='M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z'/></svg>"

st.set_page_config(
    page_title="Instagram Followers Analyzer",
    page_icon=INSTAGRAM_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# ENTIDAD DE DOMINIO
# =============================================================================

@dataclass(frozen=True)
class InstagramUser:
    """Representa un usuario de Instagram"""
    username: str

    @property
    def profile_url(self) -> str:
        return f"https://www.instagram.com/{self.username}"

    @property
    def avatar_url(self) -> str:
        """Genera avatar único usando DiceBear API"""
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={self.username}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf"

    def __hash__(self):
        return hash(self.username.lower())

    def __eq__(self, other):
        if isinstance(other, InstagramUser):
            return self.username.lower() == other.username.lower()
        return False


# =============================================================================
# FUNCIONES DE PARSEO
# =============================================================================

def parse_followers(files: List[bytes]) -> Set[InstagramUser]:
    """
    Parsea uno o más archivos followers_X.json

    Estructura esperada:
    [
      {
        "string_list_data": [
          {"value": "username", "href": "...", "timestamp": 123}
        ]
      }
    ]
    """
    users = set()
    for content in files:
        try:
            data = json.loads(content.decode('utf-8'))
            if not isinstance(data, list):
                continue
            for entry in data:
                string_list = entry.get("string_list_data", [])
                for item in string_list:
                    if value := item.get("value"):
                        users.add(InstagramUser(value.strip()))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return users


def parse_followers_with_timestamps(files: List[bytes]) -> tuple[Set[InstagramUser], Dict[str, int]]:
    """
    Parsea followers y extrae timestamps (fecha en que empezaron a seguirte)

    Returns:
        Tuple con set de usuarios y dict de username.lower() -> timestamp
    """
    users = set()
    timestamps = {}
    for content in files:
        try:
            data = json.loads(content.decode('utf-8'))
            if not isinstance(data, list):
                continue
            for entry in data:
                string_list = entry.get("string_list_data", [])
                for item in string_list:
                    if value := item.get("value"):
                        username = value.strip()
                        users.add(InstagramUser(username))
                        if ts := item.get("timestamp"):
                            timestamps[username.lower()] = ts
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return users, timestamps


def parse_following(content: bytes) -> Set[InstagramUser]:
    """
    Parsea archivo following.json

    Estructura esperada:
    {
      "relationships_following": [
        {
          "title": "username",
          "string_list_data": [{"href": "...", "timestamp": 123}]
        }
      ]
    }
    """
    users = set()
    try:
        data = json.loads(content.decode('utf-8'))
        relationships = data.get("relationships_following", [])

        if not isinstance(relationships, list):
            return users

        for entry in relationships:
            # El username está en "title"
            if title := entry.get("title"):
                users.add(InstagramUser(title.strip()))
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return users


def parse_following_with_timestamps(content: bytes) -> tuple[Set[InstagramUser], Dict[str, int]]:
    """
    Parsea following y extrae timestamps (fecha en que empezaste a seguirlos)

    Returns:
        Tuple con set de usuarios y dict de username.lower() -> timestamp
    """
    users = set()
    timestamps = {}
    try:
        data = json.loads(content.decode('utf-8'))
        relationships = data.get("relationships_following", [])

        if not isinstance(relationships, list):
            return users, timestamps

        for entry in relationships:
            if title := entry.get("title"):
                username = title.strip()
                users.add(InstagramUser(username))
                # El timestamp está en string_list_data
                string_list = entry.get("string_list_data", [])
                if string_list and (ts := string_list[0].get("timestamp")):
                    timestamps[username.lower()] = ts
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return users, timestamps


# =============================================================================
# FUNCIÓN DE ANÁLISIS
# =============================================================================

def analyze(followers: Set[InstagramUser], following: Set[InstagramUser]) -> Dict[str, Any]:
    """Analiza las relaciones entre seguidores y seguidos"""
    return {
        "not_following_back": following - followers,  # Personas que sigues pero no te siguen
        "not_followed_by_me": followers - following,  # Personas que te siguen pero no sigues
        "mutual": followers & following,              # Seguidores mutuos
        "total_followers": len(followers),
        "total_following": len(following)
    }


# =============================================================================
# GENERADOR DE EXCEL
# =============================================================================

def generate_excel(results: Dict[str, Any]) -> bytes:
    """Genera Excel con hipervínculos a los perfiles"""
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja de resumen
        summary_data = {
            "Métrica": [
                "Total Seguidores",
                "Total Seguidos",
                "No te siguen de vuelta",
                "No sigues de vuelta",
                "Seguidores mutuos"
            ],
            "Valor": [
                results["total_followers"],
                results["total_following"],
                len(results["not_following_back"]),
                len(results["not_followed_by_me"]),
                len(results["mutual"])
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Resumen", index=False)

        # Hojas de usuarios
        sheets = [
            ("No te siguen", results["not_following_back"]),
            ("No sigues", results["not_followed_by_me"]),
            ("Mutuos", results["mutual"])
        ]

        for sheet_name, users in sheets:
            if users:
                df = pd.DataFrame([
                    {
                        "Usuario": u.username,
                        "Perfil": u.profile_url
                    }
                    for u in sorted(users, key=lambda x: x.username.lower())
                ])
            else:
                df = pd.DataFrame({"Usuario": [], "Perfil": []})

            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    output.seek(0)
    return output.getvalue()


# =============================================================================
# CARGA DE ANIMACIONES LOTTIE
# =============================================================================

LOTTIE_URLS = {
    "upload": "https://lottie.host/4db68bbd-31f6-4cd8-84eb-189de081159a/IGmMCqhzpt.json",
    "success": "https://lottie.host/c5c09f7b-f3e9-4f4f-8251-5c2ac2c5e5c5/uPNMxQUdKo.json",
    "analyze": "https://lottie.host/f8c26f70-f7de-4687-b9f3-5d5c6a8e6bf3/DMVaYNrXmk.json",
}

@st.cache_data(ttl=3600)
def load_lottie(url: str):
    """Carga animación Lottie desde URL"""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


# =============================================================================
# CSS PERSONALIZADO
# =============================================================================

# =============================================================================
# CSS PERSONALIZADO (CORREGIDO PARA DARK MODE)
# =============================================================================

def load_css():
    st.markdown("""
    <style>
        /* Ocultar elementos de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Sticky topbar on scroll */
        .sticky-topbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: var(--background-color); /* Adaptable */
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 9999;
            transform: translateY(-100%);
            transition: transform 0.3s ease;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }

        .sticky-topbar.visible {
            transform: translateY(0);
        }

        .sticky-topbar .topbar-icon {
            width: 28px;
            height: 28px;
        }

        .sticky-topbar .topbar-title {
            font-size: 16px;
            font-weight: 700;
            background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }

        /* Main header with gradient text */
        .main-header {
            text-align: center;
            padding: 1.5rem 1rem 1rem;
        }

        .main-header h1 {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            line-height: 1.2;
        }

        .main-header p {
            color: var(--text-color); /* Adaptable */
            opacity: 0.8;
            font-size: 1rem;
            margin: 0.5rem 0 0 0;
        }

        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 1.6rem;
            }
            .main-header p {
                font-size: 0.9rem;
            }
        }

        /* Progress stepper - horizontal flex */
        .stepper-container {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            gap: 8px;
            padding: 16px 8px;
            flex-wrap: nowrap;
            overflow-x: auto;
        }

        .step-container {
            text-align: center;
            flex: 0 0 auto;
            min-width: 60px;
            max-width: 80px;
        }

        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin: 0 auto 6px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        .step-active {
            background: linear-gradient(45deg, #E1306C, #833AB4);
            color: white;
            animation: pulse 2s infinite;
            box-shadow: 0 4px 15px rgba(225, 48, 108, 0.4);
        }

        .step-completed {
            background: #4CAF50;
            color: white;
        }

        .step-pending {
            background: rgba(128, 128, 128, 0.2); /* Adaptable (gris transparente) */
            color: var(--text-color);
            opacity: 0.6;
        }

        .step-label {
            font-size: 11px;
            color: var(--text-color); /* Adaptable */
            opacity: 0.8;
            font-weight: 500;
            white-space: nowrap;
        }

        @media (max-width: 480px) {
            .step-circle {
                width: 32px;
                height: 32px;
                font-size: 14px;
            }
            .step-label {
                font-size: 10px;
            }
            .step-container {
                min-width: 50px;
            }
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(225, 48, 108, 0.4); }
            70% { box-shadow: 0 0 0 12px rgba(225, 48, 108, 0); }
            100% { box-shadow: 0 0 0 0 rgba(225, 48, 108, 0); }
        }

        /* Search box wrapper */
        .search-wrapper {
            position: relative;
            width: 100%;
        }

        /* User cards */
        .user-card {
            display: flex;
            align-items: center;
            padding: 14px 18px;
            margin: 10px 0;
            background: var(--secondary-background-color); /* Adaptable */
            border-radius: 16px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            transition: all 0.25s ease;
            text-decoration: none;
            color: var(--text-color) !important; /* Forzar color de texto adaptable */
            border: 1px solid rgba(128, 128, 128, 0.1); /* Borde sutil */
        }

        .user-card:hover {
            transform: translateX(8px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            border-color: #E1306C;
        }

        .user-avatar {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            margin-right: 16px;
            border: 3px solid;
            object-fit: cover;
        }

        .avatar-ghost { border-color: #FF5722; }
        .avatar-fan { border-color: #2196F3; }
        .avatar-mutual { border-color: #4CAF50; }

        .user-info {
            flex: 1;
        }

        .user-name {
            font-weight: 600;
            font-size: 15px;
            color: var(--text-color); /* Adaptable */
            margin: 0;
        }

        .user-handle {
            color: var(--text-color); /* Adaptable */
            opacity: 0.7;
            font-size: 13px;
            margin: 2px 0 0 0;
        }

        .user-date {
            display: block;
            color: #E1306C;
            font-size: 11px;
            margin-top: 4px;
            font-weight: 500;
        }

        .user-action {
            background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
            color: white !important;
            padding: 10px 18px;
            border-radius: 24px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            white-space: nowrap;
        }

        .user-action:hover {
            opacity: 0.9;
            transform: scale(1.02);
            color: white !important;
        }

        /* Download section */
        .download-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 28px;
            border-radius: 20px;
            text-align: center;
            color: white;
            margin: 16px 0;
        }

        /* Tutorial styling */
        .tutorial-step {
            background: var(--secondary-background-color); /* Adaptable */
            color: var(--text-color); /* Adaptable */
            padding: 12px 16px;
            border-radius: 12px;
            margin: 8px 0;
            border-left: 4px solid #E1306C;
            border: 1px solid rgba(128, 128, 128, 0.1);
        }
        
        /* Ajuste para enlaces dentro del tutorial */
        .tutorial-step code {
            color: #E1306C;
            background: rgba(225, 48, 108, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# COMPONENTES UI
# =============================================================================

def render_stepper(current_step: int):
    """Renderiza el progress stepper en una sola fila (HTML puro para mobile)"""
    steps = [
        ("1", "Seguidores"),
        ("2", "Seguidos"),
        ("3", "Analizar"),
        ("4", "Resultados")
    ]

    steps_html_parts = []
    for i, (num, label) in enumerate(steps):
        step_num = i + 1

        if step_num < current_step:
            status = "completed"
            icon = "✓"
        elif step_num == current_step:
            status = "active"
            icon = num
        else:
            status = "pending"
            icon = num

        steps_html_parts.append(
            f'<div class="step-container">'
            f'<div class="step-circle step-{status}">{icon}</div>'
            f'<div class="step-label">{label}</div>'
            f'</div>'
        )

    steps_html = "".join(steps_html_parts)
    html = f'<div class="stepper-container">{steps_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_tutorial():
    """Renderiza el tutorial para obtener los archivos de Instagram"""
    with st.expander("📖 ¿Cómo obtener tus archivos de Instagram?", expanded=False):
        # Link directo destacado
        st.markdown("""
        ### 🚀 Link directo para empezar:
        """)

        st.link_button(
            "📲 Ir a descargar mis datos de Instagram",
            "https://accountscenter.instagram.com/info_and_permissions/dyi/?theme=dark",
            type="primary",
            width='stretch'
        )

        st.markdown("""
        ---
        ### Pasos para configurar la descarga:

        <div class="tutorial-step">
        <strong>1.</strong> Haz clic en el botón de arriba para ir directo a la configuración de Instagram
        </div>

        <div class="tutorial-step">
        <strong>2.</strong> Selecciona <strong>"Personalizar tu descarga"</strong>
        </div>

        <div class="tutorial-step">
        <strong>3.</strong> Marca <strong>SOLO "Seguidores y seguidos"</strong> (desmarca todo lo demás)
        </div>

        <div class="tutorial-step">
        <strong>4.</strong> En <strong>Intervalo de fechas</strong> selecciona: <strong>"Desde el principio"</strong>
        </div>

        <div class="tutorial-step">
        <strong>5.</strong> En <strong>Formato</strong> selecciona: <strong>JSON</strong> (muy importante!)
        </div>

        <div class="tutorial-step">
        <strong>6.</strong> Haz clic en <strong>"Crear archivos"</strong> y espera ~5 minutos
        <br><br>
        📧 Recibirás un <strong>email de Instagram</strong> cuando esté listo para descargar
        </div>

        <div class="tutorial-step">
        <strong>7.</strong> Descarga y descomprime el ZIP. Busca la carpeta:
        <code>connections/followers_and_following/</code>
        <br><br>
        Archivos que necesitas:
        <ul>
            <li><code>followers_1.json</code> (tus seguidores)</li>
            <li><code>following.json</code> (a quienes sigues)</li>
        </ul>
        </div>

        > **💡 Tip:** Si tienes muchos seguidores, pueden haber múltiples archivos
        > (`followers_1.json`, `followers_2.json`, etc.) - ¡puedes cargarlos todos!
        """, unsafe_allow_html=True)


def format_timestamp(ts: Optional[int]) -> str:
    """Convierte timestamp Unix a fecha legible"""
    if not ts:
        return ""
    try:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%d/%m/%Y")
    except:
        return ""


def render_user_cards(users: Set[InstagramUser], category: str, color_class: str):
    """Renderiza las cards de usuarios con avatar y link"""
    if not users:
        st.info("No hay usuarios en esta categoría")
        return

    # Obtener timestamps según la categoría
    followers_ts = st.session_state.get("followers_timestamps", {})
    following_ts = st.session_state.get("following_timestamps", {})

    # Determinar qué timestamps usar para mostrar fecha en cards
    if category == "ghosts":  # No te siguen → mostrar cuándo los seguiste
        display_ts = following_ts
        date_label = "Seguido el"
    elif category == "fans":  # No sigues → mostrar cuándo te siguieron
        display_ts = followers_ts
        date_label = "Te sigue desde"
    else:  # Mutuos → mostrar el más reciente
        display_ts = {}
        for u in users:
            key = u.username.lower()
            ts1 = followers_ts.get(key, 0)
            ts2 = following_ts.get(key, 0)
            display_ts[key] = max(ts1, ts2)
        date_label = "Desde"

    # Opciones de orden
    sort_options = ["📅 Más reciente", "🔤 Nombre (A-Z)"]
    sort_key = f"sort_{category}"

    if sort_key not in st.session_state:
        st.session_state[sort_key] = sort_options[0]  # Default: más reciente

    # Controles de búsqueda y ordenación
    search_col, sort_col = st.columns([3, 1])

    with search_col:
        # Container para input + botón
        container = st.container()
        with container:
            search = st.text_input(
                "Buscar",
                key=f"search_{category}",
                placeholder="🔍 Buscar usuario...",
                label_visibility="collapsed"
            )

            st.markdown('''
                <style>
                    /* Asegura que el icono se vea bien y el texto sea legible */
                    div[data-testid="stTextInput"] input {
                        padding-right: 44px !important;
                        background-repeat: no-repeat;
                        background-position: right 12px center;
                        background-size: 18px 18px;
                        /* Icono SVG */
                        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='%23E1306C' d='M2.01 21L23 12 2.01 3 2 10l15 2-15 2z'/></svg>");
                    }
                </style>
            ''', unsafe_allow_html=True)

    with sort_col:
        sort_by = st.selectbox(
            "Ordenar",
            sort_options,
            key=sort_key,
            label_visibility="collapsed"
        )

    # Convertir a lista para ordenar
    user_list = list(users)

    # Aplicar ordenación
    if sort_by == "🔤 Nombre (A-Z)":
        user_list.sort(key=lambda u: u.username.lower())
    else:  # Más reciente (por timestamp)
        user_list.sort(key=lambda u: display_ts.get(u.username.lower(), 0), reverse=True)

    # Filtrar por búsqueda
    if search:
        user_list = [u for u in user_list if search.lower() in u.username.lower()]

    total_users = len(user_list)

    # Estado para "Ver más" - cuántos mostrar (50 por carga)
    items_key = f"items_shown_{category}"
    if items_key not in st.session_state:
        st.session_state[items_key] = 50

    items_to_show = st.session_state[items_key]
    visible_users = user_list[:items_to_show]

    # Contador
    st.caption(f"Mostrando {len(visible_users)} de {total_users} usuarios")

    # Renderizar cards
    for user in visible_users:
        ts = display_ts.get(user.username.lower())
        date_str = format_timestamp(ts)
        date_html = f'<span class="user-date">{date_label} {date_str}</span>' if date_str else ''

        st.markdown(f'''
        <a href="{user.profile_url}" target="_blank" class="user-card">
            <img src="{user.avatar_url}" class="user-avatar {color_class}" alt="{user.username}">
            <div class="user-info">
                <p class="user-name">{user.username}</p>
                <p class="user-handle">@{user.username}</p>
                {date_html}
            </div>
            <span class="user-action">Ver perfil →</span>
        </a>
        ''', unsafe_allow_html=True)

    # Botón "Ver más" si hay más usuarios
    if items_to_show < total_users:
        remaining = total_users - items_to_show
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"👇 Ver más ({remaining} restantes)",
                key=f"load_more_{category}",
                width='stretch'
            ):
                st.session_state[items_key] += 50
                st.rerun()


def render_charts(results: Dict[str, Any]):
    """Renderiza el dashboard de analítica"""
    total_followers = results["total_followers"]
    total_following = results["total_following"]
    not_following_back = len(results["not_following_back"])
    not_followed_by_me = len(results["not_followed_by_me"])
    mutual = len(results["mutual"])

    # Métricas calculadas
    follow_ratio = total_followers / total_following if total_following > 0 else 0
    engagement_rate = (mutual / total_followers * 100) if total_followers > 0 else 0
    ghost_rate = (not_following_back / total_following * 100) if total_following > 0 else 0

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📊 Ratio Seguidores/Seguidos",
            f"{follow_ratio:.2f}",
            delta="Saludable" if follow_ratio >= 1 else "Bajo",
            delta_color="normal" if follow_ratio >= 1 else "inverse"
        )

    with col2:
        st.metric(
            "🤝 Engagement Mutuo",
            f"{engagement_rate:.1f}%",
            help="% de seguidores que también sigues"
        )

    with col3:
        st.metric(
            "👻 Tasa de Ghosts",
            f"{ghost_rate:.1f}%",
            delta=f"{not_following_back} cuentas",
            delta_color="inverse",
            help="Cuentas que sigues pero no te siguen"
        )

    with col4:
        st.metric(
            "✨ Fans Únicos",
            not_followed_by_me,
            help="Te siguen pero no los sigues"
        )

    st.divider()

    # Gráficos
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Donut Chart
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Mutuos', 'No te siguen', 'No sigues'],
            values=[mutual, not_following_back, not_followed_by_me],
            hole=0.6,
            marker_colors=['#4CAF50', '#FF5722', '#2196F3'],
            textinfo='label+percent',
            textposition='outside',
            pull=[0.03, 0.03, 0]
        )])

        fig_donut.update_layout(
            title={'text': '🎯 Distribución de Relaciones', 'font': {'size': 16}},
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            annotations=[dict(
                text=f'{total_following}<br><b>Seguidos</b>',
                x=0.5, y=0.5,
                font_size=14,
                showarrow=False
            )],
            height=380,
            margin=dict(t=60, b=60, l=20, r=20)
        )

        st.plotly_chart(fig_donut, width='stretch')

    with chart_col2:
        # Bar Chart
        fig_bar = go.Figure()

        categories = ['Seguidores', 'Seguidos', 'Mutuos', 'No te siguen', 'No sigues']
        values = [total_followers, total_following, mutual, not_following_back, not_followed_by_me]
        colors = ['#E1306C', '#833AB4', '#4CAF50', '#FF5722', '#2196F3']

        fig_bar.add_trace(go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=values,
            textposition='outside'
        ))

        fig_bar.update_layout(
            title={'text': '📊 Resumen de Métricas', 'font': {'size': 16}},
            xaxis_title="",
            yaxis_title="Cantidad",
            showlegend=False,
            height=380,
            margin=dict(t=60, b=40, l=40, r=20)
        )

        st.plotly_chart(fig_bar, width='stretch')

    # Gauge de salud
    health_score = min(100, int(
        min(follow_ratio, 2) * 20 +
        engagement_rate * 0.4 +
        max(0, (100 - ghost_rate)) * 0.2
    ))

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "🏆 Puntuación de Salud", 'font': {'size': 18}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#E1306C"},
            'steps': [
                {'range': [0, 40], 'color': "#ffebee"},
                {'range': [40, 70], 'color': "#fff3e0"},
                {'range': [70, 100], 'color': "#e8f5e9"}
            ],
            'threshold': {
                'line': {'color': "#4CAF50", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))

    fig_gauge.update_layout(height=280, margin=dict(t=80, b=20))
    st.plotly_chart(fig_gauge, width='stretch')


def render_table_view(results: Dict[str, Any]):
    """Renderiza vista de tabla con links y fechas"""

    # Obtener timestamps
    followers_ts = st.session_state.get("followers_timestamps", {})
    following_ts = st.session_state.get("following_timestamps", {})

    def create_df(users: Set[InstagramUser], ts_dict: Dict[str, int], date_col_name: str) -> pd.DataFrame:
        if not users:
            return pd.DataFrame({"Usuario": [], "Fecha": [], "Perfil": []})

        data = []
        for u in users:
            ts = ts_dict.get(u.username.lower())
            date_str = format_timestamp(ts) if ts else "-"
            data.append({
                "Usuario": f"@{u.username}",
                "Fecha": date_str,
                "Perfil": u.profile_url
            })

        # Ordenar por timestamp descendente (más reciente primero)
        data.sort(key=lambda x: ts_dict.get(x["Usuario"][1:].lower(), 0), reverse=True)
        return pd.DataFrame(data)

    tab1, tab2, tab3 = st.tabs([
        f"❌ No te siguen ({len(results['not_following_back'])})",
        f"👀 No sigues ({len(results['not_followed_by_me'])})",
        f"🤝 Mutuos ({len(results['mutual'])})"
    ])

    with tab1:
        df = create_df(results["not_following_back"], following_ts, "Seguido el")
        st.dataframe(
            df,
            column_config={
                "Usuario": st.column_config.TextColumn("👤 Usuario", width="medium"),
                "Fecha": st.column_config.TextColumn("📅 Seguido el", width="small"),
                "Perfil": st.column_config.LinkColumn("🔗 Perfil", display_text="Ver →")
            },
            width='stretch',
            hide_index=True,
            height=400
        )

    with tab2:
        df = create_df(results["not_followed_by_me"], followers_ts, "Te sigue desde")
        st.dataframe(
            df,
            column_config={
                "Usuario": st.column_config.TextColumn("👤 Usuario", width="medium"),
                "Fecha": st.column_config.TextColumn("📅 Te sigue desde", width="small"),
                "Perfil": st.column_config.LinkColumn("🔗 Perfil", display_text="Ver →")
            },
            width='stretch',
            hide_index=True,
            height=400
        )

    with tab3:
        # Para mutuos, usar el timestamp más reciente
        mutual_ts = {}
        for u in results["mutual"]:
            key = u.username.lower()
            ts1 = followers_ts.get(key, 0)
            ts2 = following_ts.get(key, 0)
            mutual_ts[key] = max(ts1, ts2)

        df = create_df(results["mutual"], mutual_ts, "Desde")
        st.dataframe(
            df,
            column_config={
                "Usuario": st.column_config.TextColumn("👤 Usuario", width="medium"),
                "Fecha": st.column_config.TextColumn("📅 Desde", width="small"),
                "Perfil": st.column_config.LinkColumn("🔗 Perfil", display_text="Ver →")
            },
            width='stretch',
            hide_index=True,
            height=400
        )


def render_users_section(results: Dict[str, Any]):
    """Sección principal de exploración de usuarios"""

    # Header con título y botones de acción a la derecha
    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])

    with header_col1:
        st.subheader("👥 Explorador de Usuarios")

    with header_col2:
        excel_data = generate_excel(results)
        st.download_button(
            "📥 Descargar Excel",
            data=excel_data,
            file_name="instagram_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            width='stretch'
        )

    with header_col3:
        if st.button("🔄 Nuevo análisis", width='stretch'):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Selector de vista
    view_mode = st.radio(
        "Vista",
        ["🎴 Cards", "📋 Tabla"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if view_mode == "🎴 Cards":
        tabs = st.tabs([
            f"❌ No te siguen ({len(results['not_following_back'])})",
            f"👀 No sigues ({len(results['not_followed_by_me'])})",
            f"🤝 Mutuos ({len(results['mutual'])})"
        ])

        with tabs[0]:
            st.markdown("**Personas que sigues pero no te siguen de vuelta** - *considera dejar de seguirlas*")
            render_user_cards(results["not_following_back"], "ghosts", "avatar-ghost")

        with tabs[1]:
            st.markdown("**Personas que te siguen pero no sigues** - *considera seguirlas*")
            render_user_cards(results["not_followed_by_me"], "fans", "avatar-fan")

        with tabs[2]:
            st.markdown("**Seguidores mutuos** - *relación recíproca*")
            render_user_cards(results["mutual"], "mutuals", "avatar-mutual")
    else:
        render_table_view(results)


def render_results(results: Dict[str, Any]):
    """Página de resultados completa"""
    st.divider()

    # Dashboard de analítica
    with st.expander("📈 **Dashboard de Analítica**", expanded=True):
        render_charts(results)

    st.divider()

    # Explorador de usuarios (incluye botones de descarga y nuevo análisis)
    render_users_section(results)


# =============================================================================
# ESTADO DE LA APLICACIÓN
# =============================================================================

def init_state():
    """Inicializa el estado de la sesión"""
    defaults = {
        "followers": None,
        "following": None,
        "results": None,
        "followers_timestamps": {},  # username.lower() -> timestamp (cuando empezaron a seguirte)
        "following_timestamps": {},  # username.lower() -> timestamp (cuando empezaste a seguir)
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    load_css()
    init_state()

    # Instagram SVG for topbar
    ig_svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 448 512' class='topbar-icon'><defs><linearGradient id='ig2' x1='0%' y1='100%' x2='100%' y2='0%'><stop offset='0%' style='stop-color:#FFDC80'/><stop offset='25%' style='stop-color:#FCAF45'/><stop offset='50%' style='stop-color:#F77737'/><stop offset='75%' style='stop-color:#F56040'/><stop offset='100%' style='stop-color:#C13584'/></linearGradient></defs><path fill='url(#ig2)' d='M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z'/></svg>"""

    # Sticky topbar (aparece al hacer scroll)
    st.markdown(f"""
        <div class="sticky-topbar" id="stickyTopbar">
            {ig_svg}
            <span class="topbar-title">Instagram Followers Analyzer</span>
        </div>

        <script>
            // Show/hide sticky topbar on scroll
            window.addEventListener('scroll', function() {{
                const topbar = document.getElementById('stickyTopbar');
                if (window.scrollY > 100) {{
                    topbar.classList.add('visible');
                }} else {{
                    topbar.classList.remove('visible');
                }}
            }});
        </script>
    """, unsafe_allow_html=True)

    # Main header con texto gradient
    st.markdown("""
        <div class="main-header">
            <h1>Instagram Followers Analyzer</h1>
            <p>Descubre quién no te sigue de vuelta</p>
        </div>
    """, unsafe_allow_html=True)

    # Determinar paso actual
    step = 1
    if st.session_state.followers is not None:
        step = 2
    if st.session_state.following is not None:
        step = 3
    if st.session_state.results is not None:
        step = 4

    render_stepper(step)

    # Tutorial
    render_tutorial()

    # Sección de carga (solo si no hay resultados)
    if st.session_state.results is None:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("👥 Paso 1: Seguidores")
            st.caption("Sube uno o más archivos followers_X.json")

            followers_files = st.file_uploader(
                "Archivos de seguidores",
                type=["json"],
                accept_multiple_files=True,
                key="followers_upload",
                label_visibility="collapsed"
            )

            if followers_files:
                try:
                    contents = [f.read() for f in followers_files]
                    users, timestamps = parse_followers_with_timestamps(contents)
                    if users:
                        st.session_state.followers = users
                        st.session_state.followers_timestamps = timestamps
                        st.success(f"✅ {len(users)} seguidores cargados")
                    else:
                        st.warning("⚠️ No se encontraron usuarios en los archivos")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        with col2:
            st.subheader("➡️ Paso 2: Seguidos")
            st.caption("Sube el archivo following.json")

            following_file = st.file_uploader(
                "Archivo de seguidos",
                type=["json"],
                key="following_upload",
                label_visibility="collapsed"
            )

            if following_file:
                try:
                    users, timestamps = parse_following_with_timestamps(following_file.read())
                    if users:
                        st.session_state.following = users
                        st.session_state.following_timestamps = timestamps
                        st.success(f"✅ {len(users)} seguidos cargados")
                    else:
                        st.warning("⚠️ No se encontraron usuarios en el archivo")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        # Botón analizar
        if st.session_state.followers and st.session_state.following:
            st.divider()

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔍 Analizar", type="primary", width='stretch'):
                    with st.spinner("Analizando..."):
                        results = analyze(
                            st.session_state.followers,
                            st.session_state.following
                        )
                        st.session_state.results = results
                        st.rerun()

    # Mostrar resultados
    if st.session_state.results:
        render_results(st.session_state.results)


if __name__ == "__main__":
    main()
