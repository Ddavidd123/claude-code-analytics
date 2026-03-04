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
        print(f"Loaded {len(events)} events from {telemetry_file}")
        return events
    
    def load_employees(self, employees_file: str) -> pd.DataFrame:
        """Load employee metadata from CSV."""
        self.employees = pd.read_csv(employees_file)
        print(f"Loaded {len(self.employees)} employees from {employees_file}")
        return self.employees
    
    def normalize_events(self) -> pd.DataFrame:
        """Convert raw events to normalized DataFrame."""
        normalized = []
        
        for event in self.events:
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
        
        print(f"Normalized {len(df)} events to DataFrame")
        return df
    
    def aggregate_by_user(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate metrics by user."""
        api_requests = df[df['event_type'] == 'claude_code.api_request']
        
        if self.employees is not None:
            merged = df.merge(self.employees, left_on='user_email', right_on='email', how='left')
        else:
            merged = df
        
        agg_data = []
        for user_id in df['user_id'].unique():
            user_events = merged[merged['user_id'] == user_id]
            user_api = api_requests[api_requests['user_id'] == user_id]
            
            row = {
                'user_id': user_id,
                'user_email': user_events['user_email'].iloc[0] if len(user_events) > 0 else None,
                'num_sessions': user_events['session_id'].nunique(),
                'total_events': len(user_events),
                'total_cost_usd': user_api['cost_usd'].sum(),
                'total_api_calls': len(user_api),
                'avg_api_duration_ms': user_api['duration_ms'].mean(),
                'total_input_tokens': user_api['input_tokens'].sum(),
                'total_output_tokens': user_api['output_tokens'].sum(),
                'preferred_model': user_api['model'].mode()[0] if len(user_api) > 0 else None,
                'practice': user_events['practice'].iloc[0] if 'practice' in user_events.columns else None,
                'level': user_events['level'].iloc[0] if 'level' in user_events.columns else None,
                'location': user_events['location'].iloc[0] if 'location' in user_events.columns else None,
            }
            agg_data.append(row)
        
        df_agg = pd.DataFrame(agg_data)
        print(f"Aggregated data for {len(df_agg)} users")
        return df_agg
    
    def save_processed_data(self, df: pd.DataFrame, filename: str = "processed_events.csv"):
        """Save processed data to CSV."""
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Saved processed data to {output_path}")
        return output_path


def process_telemetry(telemetry_file: str, employees_file: str, output_dir: str = "data/processed") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main processing pipeline.
    
    Returns:
        Tuple of (events_df, users_agg_df)
    """
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
