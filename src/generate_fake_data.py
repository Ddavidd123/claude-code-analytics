#!/usr/bin/env python3
"""
Generate synthetic Claude Code telemetry data.

Produces realistic telemetry events matching the structure and distributions
of real Claude Code usage. All user identifiers are synthetic.

Usage:
    python3 generate_fake_data.py [--num-users 100] [--num-sessions 5000] [--days 60]
"""

import argparse
import csv
import hashlib
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Configuration: distributions derived from real data exploration
# ---------------------------------------------------------------------------

# Models with weights (proportional to real counts) and their stats
MODELS = {
    "claude-haiku-4-5-20251001": {
        "weight": 362,
        "avg_cost": 0.0033, "cost_std": 0.005,
        "avg_duration_ms": 5330, "duration_std": 4000,
        "avg_input_tokens": 860, "input_std": 1200,
        "avg_output_tokens": 105, "output_std": 150,
        "avg_cache_read": 7431, "cache_read_std": 15000,
        "avg_cache_create": 941, "cache_create_std": 2000,
    },
    "claude-opus-4-6": {
        "weight": 203,
        "avg_cost": 0.071, "cost_std": 0.08,
        "avg_duration_ms": 10230, "duration_std": 8000,
        "avg_input_tokens": 263, "input_std": 500,
        "avg_output_tokens": 454, "output_std": 400,
        "avg_cache_read": 73099, "cache_read_std": 50000,
        "avg_cache_create": 3149, "cache_create_std": 5000,
    },
    "claude-opus-4-5-20251101": {
        "weight": 185,
        "avg_cost": 0.084, "cost_std": 0.09,
        "avg_duration_ms": 10793, "duration_std": 8000,
        "avg_input_tokens": 61, "input_std": 200,
        "avg_output_tokens": 418, "output_std": 400,
        "avg_cache_read": 76688, "cache_read_std": 50000,
        "avg_cache_create": 5485, "cache_create_std": 8000,
    },
    "claude-sonnet-4-5-20250929": {
        "weight": 155,
        "avg_cost": 0.062, "cost_std": 0.07,
        "avg_duration_ms": 11886, "duration_std": 9000,
        "avg_input_tokens": 83, "input_std": 200,
        "avg_output_tokens": 516, "output_std": 500,
        "avg_cache_read": 68556, "cache_read_std": 50000,
        "avg_cache_create": 6483, "cache_create_std": 8000,
    },
    "claude-sonnet-4-6": {
        "weight": 21,
        "avg_cost": 0.066, "cost_std": 0.07,
        "avg_duration_ms": 9914, "duration_std": 8000,
        "avg_input_tokens": 142, "input_std": 300,
        "avg_output_tokens": 460, "output_std": 400,
        "avg_cache_read": 70715, "cache_read_std": 50000,
        "avg_cache_create": 2905, "cache_create_std": 5000,
    },
}

# Tool weights from real tool_decision data
TOOLS = {
    "Read": 190,
    "Bash": 176,
    "Edit": 79,
    "Grep": 47,
    "Glob": 29,
    "mcp_tool": 26,
    "Write": 18,
    "TodoWrite": 16,
    "TaskUpdate": 12,
    "Task": 11,
    "TaskCreate": 6,
    "AskUserQuestion": 4,
    "WebFetch": 2,
    "ToolSearch": 2,
    "WebSearch": 2,
    "NotebookEdit": 1,
    "ExitPlanMode": 1,
}

# Decision sources with weights
DECISION_SOURCES = {
    "config": 80,
    "user_temporary": 15,
    "user_permanent": 3,
    "user_reject": 2,
}

# Tool success rates (approximate from real data)
TOOL_SUCCESS_RATES = {
    "Read": 0.986,
    "Bash": 0.933,
    "Edit": 0.99,
    "Grep": 0.99,
    "Glob": 0.99,
    "mcp_tool": 0.968,
    "Write": 0.99,
    "TodoWrite": 0.99,
    "TaskUpdate": 0.99,
    "Task": 0.99,
    "TaskCreate": 0.99,
    "AskUserQuestion": 0.99,
    "WebFetch": 0.95,
    "ToolSearch": 0.99,
    "WebSearch": 0.95,
    "NotebookEdit": 0.99,
    "ExitPlanMode": 0.99,
}

# Tool average durations (ms)
TOOL_AVG_DURATIONS = {
    "Read": 34,
    "Bash": 5169,
    "Edit": 1817,
    "Grep": 474,
    "Glob": 750,
    "mcp_tool": 2531,
    "Write": 349,
    "TodoWrite": 17,
    "TaskUpdate": 1,
    "Task": 476282,
    "TaskCreate": 2,
    "AskUserQuestion": 0,
    "WebFetch": 4968,
    "ToolSearch": 1,
    "WebSearch": 193087,
    "NotebookEdit": 11,
    "ExitPlanMode": 1,
}

# API error messages with weights
API_ERRORS = [
    ("Request was aborted.", "undefined", 44),
    ("This request would exceed your account's rate limit. Please try again later.", "429", 19),
    ("output_config: Extra inputs are not permitted", "400", 6),
    ("Internal server error", "500", 4),
    ("tools: Tool names must be unique.", "400", 4),
    ("Could not load credentials from any providers", "undefined", 3),
    ("OAuth token has expired. Please obtain a new token or refresh your existing token.", "401", 2),
    ("400 The provided request is not valid", "400", 2),
]

# Scope versions with weights
SCOPE_VERSIONS = [
    ("2.1.39", 159), ("2.1.50", 151), ("2.0.76", 121), ("2.1.37", 111),
    ("2.1.45", 108), ("2.1.49", 79), ("2.1.42", 73), ("2.1.29", 69),
    ("2.1.34", 68), ("2.1.47", 67), ("2.1.56", 64), ("2.1.31", 64),
    ("2.1.12", 59), ("2.1.44", 59), ("2.1.2", 58), ("2.1.38", 54),
    ("2.1.59", 54), ("2.1.19", 48), ("2.1.20", 47), ("2.1.41", 45),
]

# Terminal types
TERMINAL_TYPES = [
    ("vscode", 40), ("pycharm", 20), ("WarpTerminal", 10),
    ("webstorm", 8), ("iTerm2", 7), ("Terminal", 5),
    ("intellij", 5), ("cursor", 3), ("goland", 2),
]

# OS types
OS_CONFIGS = [
    ({"arch": "arm64", "os_type": "darwin", "os_version": "24.6.0"}, 60),
    ({"arch": "arm64", "os_type": "darwin", "os_version": "24.5.0"}, 15),
    ({"arch": "x86_64", "os_type": "linux", "os_version": "6.1.0"}, 10),
    ({"arch": "x86_64", "os_type": "linux", "os_version": "5.15.0"}, 5),
    ({"arch": "arm64", "os_type": "darwin", "os_version": "25.0.0"}, 5),
    ({"arch": "x86_64", "os_type": "darwin", "os_version": "24.6.0"}, 3),
    ({"arch": "x86_64", "os_type": "windows", "os_version": "10.0.22631"}, 2),
]

# Engineering practices
PRACTICES = [
    "Platform Engineering",
    "Data Engineering",
    "ML Engineering",
    "Backend Engineering",
    "Frontend Engineering",
]

# Locations
LOCATIONS = [
    "United States",
    "Germany",
    "United Kingdom",
    "Poland",
    "Canada",
]

# Levels L1-L10 with weights (bell curve around L4-L6)
LEVELS = [
    ("L1", 2), ("L2", 5), ("L3", 10), ("L4", 18), ("L5", 25),
    ("L6", 20), ("L7", 10), ("L8", 5), ("L9", 3), ("L10", 2),
]

FAKE_FIRST_NAMES = [
    "alex", "jordan", "casey", "taylor", "morgan", "riley", "quinn",
    "avery", "blake", "cameron", "drew", "emery", "frankie", "harper",
    "jamie", "kai", "lennox", "max", "nico", "parker", "reese", "sage",
    "sam", "skyler", "val", "west", "eden", "phoenix", "river", "rowan",
]

FAKE_LAST_NAMES = [
    "chen", "patel", "kim", "garcia", "smith", "johnson", "lee",
    "williams", "brown", "jones", "davis", "wilson", "taylor", "martinez",
    "anderson", "thomas", "jackson", "white", "harris", "clark",
]

FAKE_HOSTNAMES = [
    "{name}s-MacBook-Pro.local", "{name}s-MacBook-Air.local",
    "MacBookPro", "{name}-dev-machine", "{name}-workstation.local",
    "dev-{name}.internal", "{name}-laptop",
]

FAKE_PROFILES = [
    "{first}", "{first}{last}", "{first}.{last}", "{first}_{last}",
    "{first[0]}{last}", "{last}", "dev-{first}",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def weighted_choice(items_with_weights):
    """Choose from list of (item, weight) tuples."""
    items, weights = zip(*items_with_weights)
    return random.choices(items, weights=weights, k=1)[0]


def positive_normal(mean, std, min_val=0):
    """Generate a positive value from a normal distribution."""
    return max(min_val, random.gauss(mean, std))


def make_deterministic_hash(seed_str):
    """Create a deterministic hash string from a seed."""
    return hashlib.sha256(seed_str.encode()).hexdigest()


def generate_fake_user(existing_emails):
    """Generate a fake user identity with employee metadata."""
    # Ensure unique email
    while True:
        first = random.choice(FAKE_FIRST_NAMES)
        last = random.choice(FAKE_LAST_NAMES)
        email = f"{first}.{last}@anthropic.com"
        if email not in existing_emails:
            existing_emails.add(email)
            break

    account_uuid = str(uuid.uuid4())
    user_id = make_deterministic_hash(email)
    org_id = str(uuid.uuid4())

    hostname_template = random.choice(FAKE_HOSTNAMES)
    name = first.capitalize()
    hostname = hostname_template.format(name=name)

    profile_template = random.choice(FAKE_PROFILES)
    profile = profile_template.format(
        first=first, last=last,
        **{"first[0]": first[0]}
    )

    serial = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10))

    os_config = weighted_choice([(c, w) for c, w in OS_CONFIGS])
    terminal = weighted_choice(TERMINAL_TYPES)
    version = weighted_choice(SCOPE_VERSIONS)

    # Employee metadata
    practice = random.choice(PRACTICES)
    level = weighted_choice(LEVELS)
    location = random.choice(LOCATIONS)
    full_name = f"{first.capitalize()} {last.capitalize()}"

    return {
        "email": email,
        "full_name": full_name,
        "account_uuid": account_uuid,
        "user_id": user_id,
        "org_id": org_id,
        "hostname": hostname,
        "profile": profile,
        "serial": serial,
        "os_config": os_config,
        "terminal": terminal,
        "version": version,
        "practice": practice,
        "level": level,
        "location": location,
    }


def make_scope(version):
    """Build scope object."""
    return {
        "name": "com.anthropic.claude_code.events",
        "version": version,
    }


def make_resource(user):
    """Build resource object."""
    return {
        "host.arch": user["os_config"]["arch"],
        "host.name": user["hostname"],
        "os.type": user["os_config"]["os_type"],
        "os.version": user["os_config"]["os_version"],
        "service.name": "claude-code-None",
        "service.version": user["version"],
        "user.email": "",
        "user.practice": user["practice"],
        "user.profile": user["profile"],
        "user.serial": user["serial"],
    }


def make_common_attributes(user, session_id, timestamp):
    """Build common attributes present in all events."""
    return {
        "event.timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.") + f"{timestamp.microsecond // 1000:03d}Z",
        "organization.id": user["org_id"],
        "session.id": session_id,
        "terminal.type": user["terminal"],
        "user.account_uuid": user["account_uuid"],
        "user.email": user["email"],
        "user.id": user["user_id"],
    }


def generate_api_request_event(user, session_id, timestamp):
    """Generate a claude_code.api_request event."""
    model_name = weighted_choice([(m, d["weight"]) for m, d in MODELS.items()])
    model = MODELS[model_name]

    input_tokens = max(0, int(positive_normal(model["avg_input_tokens"], model["input_std"])))
    output_tokens = max(1, int(positive_normal(model["avg_output_tokens"], model["output_std"])))
    cache_read = max(0, int(positive_normal(model["avg_cache_read"], model["cache_read_std"])))
    cache_create = max(0, int(positive_normal(model["avg_cache_create"], model["cache_create_std"])))
    cost = max(0, positive_normal(model["avg_cost"], model["cost_std"]))
    duration = max(100, int(positive_normal(model["avg_duration_ms"], model["duration_std"])))

    attrs = make_common_attributes(user, session_id, timestamp)
    attrs.update({
        "event.name": "api_request",
        "cache_creation_tokens": str(cache_create),
        "cache_read_tokens": str(cache_read),
        "cost_usd": str(cost),
        "duration_ms": str(duration),
        "input_tokens": str(input_tokens),
        "model": model_name,
        "output_tokens": str(output_tokens),
    })

    return {
        "body": "claude_code.api_request",
        "attributes": attrs,
        "scope": make_scope(user["version"]),
        "resource": make_resource(user),
    }


def generate_tool_decision_event(user, session_id, timestamp, tool_name=None):
    """Generate a claude_code.tool_decision event."""
    if tool_name is None:
        tool_name = weighted_choice([(t, w) for t, w in TOOLS.items()])

    source = weighted_choice([(s, w) for s, w in DECISION_SOURCES.items()])
    decision = "reject" if source == "user_reject" else "accept"

    attrs = make_common_attributes(user, session_id, timestamp)
    attrs.update({
        "event.name": "tool_decision",
        "decision": decision,
        "source": source,
        "tool_name": tool_name,
    })

    return {
        "body": "claude_code.tool_decision",
        "attributes": attrs,
        "scope": make_scope(user["version"]),
        "resource": make_resource(user),
    }


def generate_tool_result_event(user, session_id, timestamp, tool_name=None, decision_accepted=True):
    """Generate a claude_code.tool_result event."""
    if tool_name is None:
        tool_name = weighted_choice([(t, w) for t, w in TOOLS.items()])

    success_rate = TOOL_SUCCESS_RATES.get(tool_name, 0.95)
    success = random.random() < success_rate

    avg_dur = TOOL_AVG_DURATIONS.get(tool_name, 1000)
    duration = max(0, int(positive_normal(avg_dur, avg_dur * 0.8)))

    attrs = make_common_attributes(user, session_id, timestamp)
    attrs.update({
        "event.name": "tool_result",
        "decision_source": "config" if decision_accepted else "user_reject",
        "decision_type": "accept" if decision_accepted else "reject",
        "duration_ms": str(duration),
        "success": str(success).lower(),
        "tool_name": tool_name,
    })

    # Optionally add tool_result_size_bytes
    if random.random() < 0.3:
        attrs["tool_result_size_bytes"] = str(random.randint(100, 100000))

    return {
        "body": "claude_code.tool_result",
        "attributes": attrs,
        "scope": make_scope(user["version"]),
        "resource": make_resource(user),
    }


def generate_user_prompt_event(user, session_id, timestamp):
    """Generate a claude_code.user_prompt event."""
    # Prompt length: lognormal-ish distribution matching p50=128, p90=2969
    prompt_length = max(1, int(random.lognormvariate(4.85, 1.8)))

    attrs = make_common_attributes(user, session_id, timestamp)
    attrs.update({
        "event.name": "user_prompt",
        "prompt": "<REDACTED>",
        "prompt_length": str(prompt_length),
    })

    return {
        "body": "claude_code.user_prompt",
        "attributes": attrs,
        "scope": make_scope(user["version"]),
        "resource": make_resource(user),
    }


def generate_api_error_event(user, session_id, timestamp):
    """Generate a claude_code.api_error event."""
    error_msg, status_code = weighted_choice(
        [((msg, code), w) for msg, code, w in API_ERRORS]
    )
    model_name = weighted_choice([(m, d["weight"]) for m, d in MODELS.items()])
    duration = max(50, int(positive_normal(500, 600)))
    attempt = random.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0]

    attrs = make_common_attributes(user, session_id, timestamp)
    attrs.update({
        "event.name": "api_error",
        "attempt": str(attempt),
        "duration_ms": str(duration),
        "error": error_msg,
        "model": model_name,
        "status_code": status_code,
    })

    return {
        "body": "claude_code.api_error",
        "attributes": attrs,
        "scope": make_scope(user["version"]),
        "resource": make_resource(user),
    }


def generate_session_events(user, session_id, session_start):
    """Generate a realistic sequence of events for one coding session.

    A session follows a pattern:
    1. User sends a prompt
    2. Claude makes API requests and uses tools (interleaved)
    3. Occasionally errors occur
    4. Repeat for multiple turns
    """
    events = []
    num_turns = random.randint(1, 5)
    
    for turn in range(num_turns):
        # User sends prompt
        timestamp = session_start + timedelta(seconds=random.randint(1, 300))
        events.append(generate_user_prompt_event(user, session_id, timestamp))
        
        # Claude processes: 0-15 tool decisions/results
        num_tools = random.randint(0, 15)
        tool_accepted = random.random() > 0.1  # 90% accept rate
        
        for _ in range(num_tools):
            timestamp = timestamp + timedelta(seconds=random.randint(1, 50))
            tool_name = weighted_choice([(t, w) for t, w in TOOLS.items()])
            
            events.append(generate_tool_decision_event(user, session_id, timestamp, tool_name))
            timestamp = timestamp + timedelta(seconds=random.randint(1, 20))
            events.append(generate_tool_result_event(user, session_id, timestamp, tool_name, tool_accepted))
        
        # API request
        timestamp = timestamp + timedelta(seconds=random.randint(1, 10))
        if random.random() < 0.95:  # 95% success rate
            events.append(generate_api_request_event(user, session_id, timestamp))
        else:
            events.append(generate_api_error_event(user, session_id, timestamp))
    
    return events


def events_to_log_batches(events, batch_size_range=(1, 10)):
    """Group events into log batches."""
    batches = []
    batch_size = random.randint(*batch_size_range)
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        batch_obj = {
            "logEvents": [
                {"message": json.dumps(event, separators=(',', ':'))}
                for event in batch
            ]
        }
        batches.append(batch_obj)
    
    return batches


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Claude Code telemetry data")
    parser.add_argument("--num-users", type=int, default=30, help="Number of engineers")
    parser.add_argument("--num-sessions", type=int, default=500, help="Total coding sessions")
    parser.add_argument("--days", type=int, default=30, help="Time span in days")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    random.seed(args.seed)

    print(f"Generating {args.num_users} users with {args.num_sessions} sessions over {args.days} days...")

    # Generate users
    users = []
    existing_emails = set()
    for _ in range(args.num_users):
        users.append(generate_fake_user(existing_emails))

    # Generate sessions
    start_date = datetime.now(timezone.utc) - timedelta(days=args.days)
    all_events = []

    for _ in range(args.num_sessions):
        user = random.choice(users)
        session_id = str(uuid.uuid4())
        session_start = start_date + timedelta(
            days=random.randint(0, args.days),
            seconds=random.randint(0, 86400)
        )
        
        session_events = generate_session_events(user, session_id, session_start)
        all_events.extend(session_events)

    # Write telemetry logs
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    with open(os.path.join(args.output_dir, "telemetry_logs.jsonl"), "w") as f:
        batches = events_to_log_batches(all_events)
        for batch in batches:
            f.write(json.dumps(batch) + "\n")

    print(f"Generated {len(all_events)} events in {len(batches)} batches")

    # Write employees CSV
    with open(os.path.join(args.output_dir, "employees.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "full_name", "practice", "level", "location"])
        writer.writeheader()
        for user in users:
            writer.writerow({
                "email": user["email"],
                "full_name": user["full_name"],
                "practice": user["practice"],
                "level": user["level"],
                "location": user["location"],
            })

    print(f"Generated {len(users)} employees")
    print(f"Output written to {args.output_dir}/")


if __name__ == "__main__":
    main()
