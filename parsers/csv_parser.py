"""Parser de archivos CSV de reportes semanales de sesiones de Data Protector."""

import csv
import io
from models.report_data import SessionRecord, CellManagerReport


def parse_csv_file(file_path: str) -> list[SessionRecord]:
    """Parsea un archivo CSV de reporte semanal de sesiones.

    El formato de Data Protector usa TSV con headers en la línea 8:
    Session Type, Specification, Status, Mode, Start Time, ...
    """
    sessions = []

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Encontrar la línea de headers (empieza con "# Session Type")
    header_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("# Session Type"):
            header_line_idx = i
            break

    if header_line_idx is None:
        return sessions

    # Parsear headers
    header_raw = lines[header_line_idx].lstrip("# ").strip()
    headers = header_raw.split("\t")

    # Parsear datos (líneas después del header)
    for line in lines[header_line_idx + 1:]:
        line = line.strip()
        if not line:
            continue

        fields = line.split("\t")
        if len(fields) < 10:
            continue

        try:
            gb_written = float(fields[10]) if len(fields) > 10 and fields[10] else 0.0
        except (ValueError, IndexError):
            gb_written = 0.0

        try:
            errors = int(fields[12]) if len(fields) > 12 and fields[12] else 0
        except (ValueError, IndexError):
            errors = 0

        try:
            failed_da = int(fields[16]) if len(fields) > 16 and fields[16] else 0
        except (ValueError, IndexError):
            failed_da = 0

        try:
            completed_da = int(fields[17]) if len(fields) > 17 and fields[17] else 0
        except (ValueError, IndexError):
            completed_da = 0

        success_val = fields[20].strip() if len(fields) > 20 else "0%"

        # Intentar parsear fecha
        dt_obj = None
        start_time_str = fields[4].strip() if len(fields) > 4 else ""
        if start_time_str:
            try:
                # Formato esperado Data Protector: "MM/DD/YYYY HH:MM:SS AM/PM"
                # Pero puede variar según locale. Usamos dateutil si estuviera o try formats.
                # Asumimos formato MDY primero, luego DMY
                from dateutil import parser
                dt_obj = parser.parse(start_time_str)
            except ImportError:
                 # Fallback básico si no hay dateutil (pandas lo suele instalar pero por si acaso)
                 from datetime import datetime
                 try:
                     dt_obj = datetime.strptime(start_time_str, "%m/%d/%Y %I:%M:%S %p")
                 except ValueError:
                     try:
                         dt_obj = datetime.strptime(start_time_str, "%d/%m/%Y %H:%M:%S")
                     except ValueError:
                         pass
            except Exception:
                pass

        session = SessionRecord(
            session_type=fields[0].strip() if len(fields) > 0 else "",
            specification=fields[1].strip() if len(fields) > 1 else "",
            status=fields[2].strip() if len(fields) > 2 else "",
            mode=fields[3].strip() if len(fields) > 3 else "",
            start_time=start_time_str,
            end_time=fields[6].strip() if len(fields) > 6 else "",
            duration=fields[9].strip() if len(fields) > 9 else "",
            gb_written=gb_written,
            errors=errors,
            failed_da=failed_da,
            completed_da=completed_da,
            success=success_val,
            session_id=fields[22].strip() if len(fields) > 22 else "",
            start_datetime=dt_obj,
        )
        sessions.append(session)

    return sessions


def parse_multiple_csvs(file_paths: list[str], cell_manager_name: str) -> CellManagerReport:
    """Procesa múltiples CSVs de un mismo Cell Manager y genera el resumen."""
    all_sessions = []

    for fp in file_paths:
        sessions = parse_csv_file(fp)
        all_sessions.extend(sessions)

    # Calcular métricas
    unique_specs = set()
    total_gb = 0.0
    successful_jobs = 0

    for s in all_sessions:
        unique_specs.add(s.specification)
        total_gb += s.gb_written
        # Un job es "exitoso" si su Success no es "0%"
        if s.success and s.success.strip() != "0%":
            successful_jobs += 1

    total_jobs = len(all_sessions)
    compliance = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0

    return CellManagerReport(
        cell_manager=cell_manager_name,
        total_policies=len(unique_specs),
        total_jobs=total_jobs,
        size_tb=round(total_gb / 1024, 2),
        compliance_pct=round(compliance, 2),
        sessions=all_sessions,
    )
