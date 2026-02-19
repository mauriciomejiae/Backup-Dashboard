"""Modelos de datos para reportes de backup."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionRecord:
    """Registro individual de una sesión de backup desde CSV."""
    session_type: str = ""
    specification: str = ""
    status: str = ""
    mode: str = ""
    start_time: str = ""
    end_time: str = ""
    duration: str = ""
    gb_written: float = 0.0
    errors: int = 0
    warnings: int = 0
    failed_da: int = 0
    completed_da: int = 0
    objects: int = 0
    success: str = "0%"
    success: str = "0%"
    session_id: str = ""
    start_datetime: Optional[object] = None  # datetime object for filtering


@dataclass
class CellManagerReport:
    """Resumen procesado de un Cell Manager desde los CSVs."""
    cell_manager: str = ""
    total_policies: int = 0
    total_jobs: int = 0
    size_tb: float = 0.0
    compliance_pct: float = 0.0
    sessions: list = field(default_factory=list)


@dataclass
class ScheduleRow:
    """Fila de datos del Schedule para un Cell Manager/plataforma."""
    platform: str = ""
    ejecutados: int = 0
    programados: int = 0
    relanzados: int = 0
    fallidos: int = 0
    q: int = 0  # Fallidos gestionados/resueltos (OLD logic based on Q)
    gestionados: int = 0  # Fallidos gestionados (NEW logic)
    kpi_operacion: float = 0.0
    pct_relanzamiento: float = 0.0
    gestion_fallidos: float = 0.0


@dataclass
class ScheduleReport:
    """Reporte completo del Schedule mensual."""
    period_name: str = ""
    rows: list = field(default_factory=list)  # List[ScheduleRow]
    total_ejecutados: int = 0
    total_programados: int = 0
    total_relanzados: int = 0
    total_fallidos: int = 0
    total_q: int = 0
    kpi_operacion_general: float = 0.0
    kpi_gestion_fallidos_general: float = 0.0
    pct_relanzados_general: float = 0.0
