"""Session store for diagnostic records - monthly CSV storage."""

import csv
from datetime import datetime
from pathlib import Path

from dte_diagnostic_agent.storage.models import SessionRecord, SessionStatus


class SessionStore:
    """Diagnostic session storage with monthly CSV files.
    
    File format: sessions_YYYY-MM.csv
    Storage path: {session_dir}/sessions_YYYY-MM.csv
    """
    
    CSV_HEADERS = [
        "session_id",
        "description",
        "cluster_name",
        "status",
        "created_at",
        "updated_at",
        "completed_at",
        "problem_category",
        "severity",
        "top_hypothesis",
        "confidence",
        "error_message",
    ]
    
    def __init__(self, session_dir: str = "./data/sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._current_month_cache: dict[str, SessionRecord] = {}
        self._load_current_month()
    
    def _get_month_file(self, date: datetime) -> Path:
        month_str = date.strftime("%Y-%m")
        return self.session_dir / f"sessions_{month_str}.csv"
    
    def _load_current_month(self) -> None:
        current_file = self._get_month_file(datetime.now())
        if current_file.exists():
            self._current_month_cache = self._load_from_file(current_file)
    
    def _load_from_file(self, file_path: Path) -> dict[str, SessionRecord]:
        records = {}
        if not file_path.exists():
            return records
        
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    record = SessionRecord.from_csv_row(row)
                    records[record.session_id] = record
                except Exception as e:
                    print(f"Warning: Failed to parse record: {e}")
        
        return records
    
    def _save_to_file(self, file_path: Path, records: dict[str, SessionRecord]) -> None:
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            for record in records.values():
                writer.writerow(record.to_csv_row())
    
    async def create(self, record: SessionRecord) -> SessionRecord:
        """Create a new session record.
        
        If the record is for a different month, it will be saved to that month's file.
        """
        month_file = self._get_month_file(record.created_at)
        
        if month_file == self._get_month_file(datetime.now()):
            self._current_month_cache[record.session_id] = record
            self._save_to_file(month_file, self._current_month_cache)
        else:
            month_records = self._load_from_file(month_file)
            month_records[record.session_id] = record
            self._save_to_file(month_file, month_records)
        
        return record
    
    async def get(self, session_id: str) -> SessionRecord | None:
        """Get a session record by ID."""
        if session_id in self._current_month_cache:
            return self._current_month_cache[session_id]
        
        for csv_file in self.session_dir.glob("sessions_*.csv"):
            records = self._load_from_file(csv_file)
            if session_id in records:
                return records[session_id]
        
        return None
    
    async def update(self, session_id: str, **updates) -> SessionRecord | None:
        """Update a session record."""
        record = await self.get(session_id)
        if not record:
            return None
        
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        record.updated_at = datetime.now()
        
        month_file = self._get_month_file(record.created_at)
        if month_file == self._get_month_file(datetime.now()):
            self._current_month_cache[session_id] = record
            self._save_to_file(month_file, self._current_month_cache)
        else:
            month_records = self._load_from_file(month_file)
            month_records[session_id] = record
            self._save_to_file(month_file, month_records)
        
        return record
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session record."""
        if session_id in self._current_month_cache:
            del self._current_month_cache[session_id]
            month_file = self._get_month_file(datetime.now())
            self._save_to_file(month_file, self._current_month_cache)
            return True
        
        for csv_file in self.session_dir.glob("sessions_*.csv"):
            records = self._load_from_file(csv_file)
            if session_id in records:
                del records[session_id]
                self._save_to_file(csv_file, records)
                return True
        
        return False
    
    async def list_all(
        self,
        status_filter: SessionStatus | None = None,
        cluster: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SessionRecord], int]:
        """List all session records with filters."""
        all_records = []
        
        for csv_file in sorted(self.session_dir.glob("sessions_*.csv"), reverse=True):
            records = self._load_from_file(csv_file)
            all_records.extend(records.values())
        
        filtered = []
        for record in all_records:
            if status_filter and record.status != status_filter:
                continue
            if cluster and record.cluster_name != cluster:
                continue
            if start_date and record.created_at < start_date:
                continue
            if end_date and record.created_at > end_date:
                continue
            filtered.append(record)
        
        filtered.sort(key=lambda r: r.created_at, reverse=True)
        
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        
        return paginated, total
    
    async def list_by_month(self, year: int, month: int) -> list[SessionRecord]:
        """List all records for a specific month."""
        month_file = self.session_dir / f"sessions_{year}-{month:02d}.csv"
        if not month_file.exists():
            return []
        
        records = self._load_from_file(month_file)
        return list(records.values())
    
    async def get_statistics(self, year: int | None = None, month: int | None = None) -> dict:
        """Get statistics for sessions."""
        if year and month:
            records = await self.list_by_month(year, month)
        else:
            records, _ = await self.list_all(limit=10000)
        
        stats = {
            "total": len(records),
            "by_status": {},
            "by_cluster": {},
            "by_category": {},
        }
        
        for record in records:
            status_key = record.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            if record.cluster_name:
                stats["by_cluster"][record.cluster_name] = stats["by_cluster"].get(record.cluster_name, 0) + 1
            
            if record.problem_category:
                stats["by_category"][record.problem_category] = stats["by_category"].get(record.problem_category, 0) + 1
        
        return stats
    
    def get_available_months(self) -> list[str]:
        """Get list of available month files."""
        months = []
        for csv_file in self.session_dir.glob("sessions_*.csv"):
            month_str = csv_file.stem.replace("sessions_", "")
            months.append(month_str)
        return sorted(months, reverse=True)