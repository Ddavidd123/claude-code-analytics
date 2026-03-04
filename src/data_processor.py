"""
Data Processing Pipeline for Claude Code Telemetry

Transforms raw telemetry events into structured analytics-ready data.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple


class TelemetryProcessor:
    """Process raw telemetry logs into structured datasets."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.events = []
        self.employees = None
    
    def load_raw_logs(self, telemetry_file: str) -> List[Dict]:
        """Load telemetry logs from JSONL file."""
        events = []
        with open(telemetry_file, 'r') as f:
            for line in f:
                batch = json.loads(line)
                for log_event in batch.get('logEvents', []):
                    event = json.loads(log_event['message'])
                    events.append(event)
        
        self.events = events
        return events
    
    def load_employees(self, employees_file: str) -> pd.DataFrame:
        """Load employee metadata from CSV."""
        self.employees = pd.read_csv(employees_file)
        return self.employees
    
    def normalize_events(self) -> pd.DataFrame:
        """Convert raw events to normalized DataFrame - optimized for large datasets."""
        normalized = []
        
        for i, event in enumerate(self.events):
            
            body = event.get('body', '')
            attrs = event.get('attributes', {})
            
            # Extract common fields
            normalized_row = {
                'event_type': body,
                'timestamp': attrs.get('event.timestamp'),
                'user_id': attrs.get('user.id'),
                'user_email': attrs.get('user.email'),
                'session_id': attrs.get('session.id'),
                'organization_id': attrs.get('organization.id'),
                'event_name': attrs.get('event.name'),
                'terminal_type': attrs.get('terminal.type'),
            }
            
            # Event-specific fields
            if body == 'claude_code.api_request':
                normalized_row.update({
                    'model': attrs.get('model'),
                    'cost_usd': float(attrs.get('cost_usd', 0)),
                    'duration_ms': int(attrs.get('duration_ms', 0)),
                    'input_tokens': int(attrs.get('input_tokens', 0)),
                    'output_tokens': int(attrs.get('output_tokens', 0)),
                    'cache_read_tokens': int(attrs.get('cache_read_tokens', 0)),
                    'cache_creation_tokens': int(attrs.get('cache_creation_tokens', 0)),
                })
            elif body == 'claude_code.tool_decision':
                normalized_row.update({
                    'tool_name': attrs.get('tool_name'),
                    'decision': attrs.get('decision'),
                    'source': attrs.get('source'),
                })
            elif body == 'claude_code.tool_result':
                normalized_row.update({
                    'tool_name': attrs.get('tool_name'),
                    'success': attrs.get('success') == 'true',
                    'duration_ms': int(attrs.get('duration_ms', 0)),
                    'tool_result_size_bytes': int(attrs.get('tool_result_size_bytes', 0)),
                })
            elif body == 'claude_code.user_prompt':
                normalized_row.update({
                    'prompt_length': int(attrs.get('prompt_length', 0)),
                })
            elif body == 'claude_code.api_error':
                normalized_row.update({
                    'model': attrs.get('model'),
                    'error': attrs.get('error'),
                    'status_code': attrs.get('status_code'),
                    'attempt': int(attrs.get('attempt', 1)),
                })
            
            normalized.append(normalized_row)
        
        df = pd.DataFrame(normalized)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        return df
    
    def aggregate_by_user(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate metrics by user - optimized version."""
        api_requests = df[df['event_type'] == 'claude_code.api_request']
        
        # Create email->employee metadata dict for fast lookup
        emp_dict = {}
        if self.employees is not None:
            emp_dict = self.employees.set_index('email').to_dict('index')
        
        agg_data = []
        user_ids = df['user_id'].unique()
        
        for i, user_id in enumerate(user_ids):
                
            user_events = df[df['user_id'] == user_id]
            user_api = api_requests[api_requests['user_id'] == user_id]
            
            email = user_events['user_email'].iloc[0] if len(user_events) > 0 else None
            
            # Get employee metadata from dict instead of merge
            emp_meta = emp_dict.get(email, {}) if email else {}
            
            row = {
                'user_id': user_id,
                'user_email': email,
                'num_sessions': user_events['session_id'].nunique(),
                'total_events': len(user_events),
                'total_cost_usd': user_api['cost_usd'].sum(),
                'total_api_calls': len(user_api),
                'avg_api_duration_ms': user_api['duration_ms'].mean(),
                'total_input_tokens': user_api['input_tokens'].sum(),
                'total_output_tokens': user_api['output_tokens'].sum(),
                'preferred_model': user_api['model'].mode()[0] if len(user_api) > 0 else None,
                'practice': emp_meta.get('practice'),
                'level': emp_meta.get('level'),
                'location': emp_meta.get('location'),
            }
            agg_data.append(row)
        
        df_agg = pd.DataFrame(agg_data)
        return df_agg
    
    def save_processed_data(self, df: pd.DataFrame, filename: str = "processed_events.csv"):
        """Save processed data to CSV."""
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        return output_path


def process_telemetry(
    telemetry_file: str,
    employees_file: str,
    output_dir: str = "data/processed",
    force_reprocess: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main processing pipeline.
    
    Optimized: if processed CSV files exist, load them directly instead of reprocessing.
    
    Returns:
        Tuple of (events_df, users_agg_df)
    """
    output_path = Path(output_dir)
    events_csv = output_path / "normalized_events.csv"
    users_csv = output_path / "users_aggregated.csv"
    telemetry_path = Path(telemetry_file)
    employees_path = Path(employees_file)
    
    # Fast path: if cache exists and is up‑to‑date vs raw inputs, use it
    if not force_reprocess and events_csv.exists() and users_csv.exists():
        try:
            # If processed CSVs are newer than *both* source files, trust the cache
            cache_mtime = min(events_csv.stat().st_mtime, users_csv.stat().st_mtime)
            src_mtime = max(telemetry_path.stat().st_mtime, employees_path.stat().st_mtime)
            if cache_mtime >= src_mtime:
                events_df = pd.read_csv(events_csv)
                users_df = pd.read_csv(users_csv)
                return events_df, users_df
        except Exception:
            # Any failure falls back to full reprocessing
            pass
    
    # Slow path: process from raw JSONL
    processor = TelemetryProcessor(output_dir)
    
    # Load raw data
    processor.load_raw_logs(telemetry_file)
    processor.load_employees(employees_file)
    
    # Transform
    events_df = processor.normalize_events()
    users_agg_df = processor.aggregate_by_user(events_df)
    
    # Save
    processor.save_processed_data(events_df, "normalized_events.csv")
    processor.save_processed_data(users_agg_df, "users_aggregated.csv")
    
    return events_df, users_agg_df
