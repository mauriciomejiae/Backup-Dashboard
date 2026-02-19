"""Utilidades de cálculo para KPIs y métricas."""


def format_pct(value: float) -> str:
    """Formatea un porcentaje con 2 decimales."""
    return f"{value:.2f}%"


def format_tb(value: float) -> str:
    """Formatea tamaño en TB con 2 decimales."""
    return f"{value:.2f} TB"


def get_compliance_color(pct: float) -> str:
    """Retorna color según nivel de cumplimiento."""
    if pct >= 98:
        return "#00e676"  # Verde
    elif pct >= 95:
        return "#ffab00"  # Amarillo
    elif pct >= 90:
        return "#ff6d00"  # Naranja
    else:
        return "#ff1744"  # Rojo


def get_kpi_color(pct: float) -> str:
    """Retorna color según nivel de KPI."""
    if pct >= 97:
        return "#00e676"
    elif pct >= 90:
        return "#ffab00"
    elif pct >= 80:
        return "#ff6d00"
    else:
        return "#ff1744"
