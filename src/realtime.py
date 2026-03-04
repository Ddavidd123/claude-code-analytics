"""
Utilities demonstrating real-time ingestion of telemetry data.

This module includes a simple file-watching class (based on watchdog) that
invokes a callback whenever new lines are appended to the telemetry log.
Another helper simulates a live stream by periodically generating events
using the same generator used in data generation.
"""

import time
import threading
import json
import random
import uuid
from typing import Callable, List
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .generate_fake_data import (
    generate_user_prompt_event, generate_api_request_event,
    generate_tool_decision_event, generate_tool_result_event,
    generate_api_error_event, generate_fake_user
)
from .data_processor import TelemetryProcessor


class TailHandler(FileSystemEventHandler):
    """Handler that calls callback with new lines appended to a file."""
    def __init__(self, file_path: Path, callback: Callable[[str], None]):
        self.file_path = file_path
        self.callback = callback
        self._position = file_path.stat().st_size if file_path.exists() else 0

    def on_modified(self, event):
        if Path(event.src_path) == self.file_path:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(self._position)
                for line in f:
                    self.callback(line.strip())
                self._position = f.tell()


class LiveTelemetryStream:
    """Demonstrates live streaming by watching a telemetry file."""

    def __init__(self, telemetry_file: Path, processor: TelemetryProcessor):
        self.telemetry_file = telemetry_file
        self.processor = processor
        self.observer = Observer()

    def start(self, callback: Callable[[List[dict]], None]):
        """Begin watching the file and processing events.

        'callback' will receive a list of parsed events whenever new data arrives.
        """
        handler = TailHandler(self.telemetry_file, self._on_new_line)
        self._consumer = callback
        self.observer.schedule(handler, str(self.telemetry_file.parent), recursive=False)
        self.observer.start()

    def _on_new_line(self, line: str):
        try:
            batch = json.loads(line)
            events = [json.loads(item['message']) for item in batch.get('logEvents', [])]
        except Exception:
            return
        # Append new events to processor state and process incrementally
        if not hasattr(self.processor, "events") or self.processor.events is None:
            self.processor.events = []
        self.processor.events.extend(events)
        df = self.processor.normalize_events()
        self._consumer(events)

    def stop(self):
        self.observer.stop()
        self.observer.join()


# small example generator that writes events to file continuously

def simulate_stream(output_file: Path, interval: float = 1.0):
    """Append synthetic events to `output_file` indefinitely (CTRL-C to stop)."""
    from datetime import datetime, timezone
    
    users = []
    existing = set()
    for _ in range(10):
        users.append(generate_fake_user(existing))

    session_ids = {u['user_id']: str(uuid.uuid4()) for u in users}

    with open(output_file, 'a', encoding='utf-8') as f:
        while True:
            user = random.choice(users)
            sid = session_ids[user['user_id']]
            timestamp = datetime.now(timezone.utc)
            
            # create one random event
            event = generate_user_prompt_event(user, sid, timestamp)
            batch = {"logEvents": [{"message": json.dumps(event)}]}
            f.write(json.dumps(batch) + "\n")
            f.flush()
            time.sleep(interval)
