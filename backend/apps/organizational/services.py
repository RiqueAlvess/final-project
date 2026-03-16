"""CSV import service for organizational hierarchy."""

from __future__ import annotations

import csv
import io
import logging
from typing import TYPE_CHECKING

from .models import CSVImport, Registro, Setor, Unidade

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    User = get_user_model()

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {'EMAIL', 'UNIDADE', 'SETOR'}


class CSVImportService:
    """Parses and persists organizational hierarchy records from a CSV file."""

    def __init__(self, file_name: str, file_content: bytes, imported_by=None) -> None:
        self.file_name = file_name
        self.file_content = file_content
        self.imported_by = imported_by

    def process(self) -> CSVImport:
        """
        Run the full import pipeline:
        1. Validate headers
        2. Parse rows
        3. Persist records
        4. Return the CSVImport tracking object
        """
        csv_import = CSVImport.objects.create(
            file_name=self.file_name,
            status=CSVImport.Status.PROCESSING,
            imported_by=self.imported_by,
        )

        try:
            rows, header_error = self._parse_csv()
            if header_error:
                csv_import.status = CSVImport.Status.FAILED
                csv_import.errors = [header_error]
                csv_import.save(update_fields=['status', 'errors'])
                return csv_import

            csv_import.total_rows = len(rows)
            errors: list[dict] = []
            success_count = 0

            for idx, row in enumerate(rows, start=2):  # start=2: row 1 is header
                try:
                    self._persist_row(row, csv_import)
                    success_count += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append({'row': idx, 'data': row, 'error': str(exc)})

            csv_import.successful_rows = success_count
            csv_import.failed_rows = len(errors)
            csv_import.errors = errors
            csv_import.status = CSVImport.Status.COMPLETED
            csv_import.save(update_fields=['total_rows', 'successful_rows', 'failed_rows', 'errors', 'status'])

        except Exception as exc:  # noqa: BLE001
            logger.exception('Unexpected error during CSV import: %s', exc)
            csv_import.status = CSVImport.Status.FAILED
            csv_import.errors = [str(exc)]
            csv_import.save(update_fields=['status', 'errors'])

        return csv_import

    # ──────────────────────────────────────────────────────────────────────────

    def _parse_csv(self) -> tuple[list[dict], str | None]:
        """Decode, read and validate CSV content. Returns (rows, error_message)."""
        try:
            text = self.file_content.decode('utf-8-sig')  # handle BOM
        except UnicodeDecodeError:
            text = self.file_content.decode('latin-1')

        reader = csv.DictReader(io.StringIO(text))

        if reader.fieldnames is None:
            return [], 'CSV file appears to be empty.'

        normalized = {col.strip().upper() for col in reader.fieldnames}
        missing = REQUIRED_COLUMNS - normalized
        if missing:
            return [], f'Missing required columns: {", ".join(sorted(missing))}. Expected: EMAIL, UNIDADE, SETOR.'

        rows = [
            {k.strip().upper(): v.strip() for k, v in row.items() if k}
            for row in reader
        ]
        # Skip completely blank rows
        rows = [r for r in rows if any(r.values())]
        return rows, None

    def _persist_row(self, row: dict, csv_import: CSVImport) -> Registro:
        """Create or update a Registro for a single CSV row."""
        email = row.get('EMAIL', '').strip().lower()
        unidade_name = row.get('UNIDADE', '').strip()
        setor_name = row.get('SETOR', '').strip()

        if not email:
            raise ValueError('EMAIL is required.')
        if not unidade_name:
            raise ValueError('UNIDADE is required.')
        if not setor_name:
            raise ValueError('SETOR is required.')

        unidade, _ = Unidade.objects.get_or_create(name=unidade_name)
        setor, _ = Setor.objects.get_or_create(name=setor_name, unidade=unidade)

        registro, _ = Registro.objects.update_or_create(
            email=email,
            unidade=unidade,
            setor=setor,
            defaults={'csv_import': csv_import},
        )
        return registro
