# Instagram Followers Analyzer

Proyecto para analizar seguidores de Instagram y ofrecer métricas y reportes simples mediante una interfaz Streamlit.

**Estado:** Prototipo / herramienta personal
**Streamlit-app:** https://instagram-followers-analyzer.streamlit.app/

## Descripción

Este repositorio contiene una pequeña aplicación en Python (Streamlit) pensada para analizar información relacionada con seguidores de cuentas de Instagram. La intención es proporcionar una interfaz rápida y reproducible para cargar datos, ejecutar análisis básicos y generar insights sobre crecimiento, engagement y seguidores mutuos/no mutuos.

El proyecto está diseñado como una base extensible para experimentos y herramientas internas; puede adaptarse a análisis más avanzados o integrarse con APIs y pipelines de datos.

## Características principales

- Interfaz web ligera con Streamlit (`app.py`).
- Flujo de instalación rápido con `requirements.txt`.
- Tests básicos con `pytest` (`test_app.py`).
- Buenas prácticas para desarrollo local

## Estructura del repositorio

- `app.py` — aplicación principal de Streamlit.
- `requirements.txt` — dependencias del proyecto.
- `test_app.py` — pruebas unitarias básicas.
- `.gitignore` — reglas de exclusión (incluye `.streamlit/`).

## Requisitos

- Python 3.10+ recomendado.
- `pip` para instalar dependencias.
- (Opcional) `virtualenv` o `venv` para entornos aislados.

## Instalación (local)

1. Clona el repositorio:

```bash
git clone <repo-url>
cd instagram-followers-analyzer
```

2. Crea y activa un entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

## Configuración

Streamlit usa la carpeta `.streamlit/` para configuración local

## Uso

Ejecuta la app Streamlit:

```bash
streamlit run app.py
```

Parámetros útiles:

- `--server.port <port>` para especificar puerto.
- `--server.headless true` para entornos sin interfaz gráfica.

## Tests

Ejecuta las pruebas con `pytest`:

```bash
pytest -q
```

Agrega más pruebas conforme se amplíe la lógica.

## Desarrollo y contribución

- Sigue el flujo: branch feature -> pull request -> revisión.
- Mantén las dependencias en `requirements.txt` actualizadas.
- Escribe pruebas para nuevas funcionalidades.

Si te interesa colaborar, abre un issue o un pull request con una descripción clara del cambio.