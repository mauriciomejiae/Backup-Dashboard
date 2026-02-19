# Backup Dashboard

## Descripción General

Plataforma analítica centralizada para Data Protector Cell Managers. Procesa reportes de sesiones para visualizar SLAs, eficiencia operativa y salud de la infraestructura.

## Capacidades Principales

- **Analítica de KPI:** Cálculo automatizado de tasas de Éxito/Fallo y Ventanas de Backup.
- **Integración Multi-Fuente:** Ingesta y normalización de datos de múltiples Cell Managers.
- **Inteligencia de Cronogramas:** Correlación entre cronogramas planificados y ejecuciones reales para detección de "Missed Jobs".
- **Acceso Seguro:** Sistema de autenticación integrado para control de acceso administrativo.

## Stack Tecnológico

- **Backend:** Python 3.10+
- **Frontend:** Streamlit
- **Procesamiento de Datos:** Pandas
- **Parsing:** OpenPyXL

## Despliegue

### Requisitos Previos

- Python 3.10+
- Reportes de Data Protector (CSV/Excel)

### Instalación

1. Clonar repositorio:

   ```powershell
   git clone https://github.com/mauriciomejiae/Backup-Dashboard.git
   cd Backup-Dashboard
   ```

2. Configurar entorno virtual:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Instalar dependencias:

   ```powershell
   pip install -r requirements.txt
   ```

4. Configurar secretos en `.streamlit/secrets.toml`:

   ```toml
   [auth]
   username = "user"
   password = "*********"
   ```

5. Iniciar aplicación:
   ```powershell
   streamlit run main.py
   ```

## Estructura de Directorios

```text
root/
├── .streamlit/     # Secretos y configuración visual
├── models/         # Definiciones de objetos de datos
├── parsers/        # Lógica de extracción y normalización
├── utils/          # Funciones auxiliares
├── views/          # Componentes de UI
└── main.py         # Punto de entrada
```
