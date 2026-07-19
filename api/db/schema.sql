-- hosts table
-- Represents anything Sentinel monitors: a bare-metal machine, a VM,
-- an LXC container, or a Docker container. We use one table for all
-- of these (instead of separate tables) because they share the same
-- core fields, and this lets us model parent/child relationships
-- (e.g. a Docker container running inside a VM) with a single
-- self-referencing foreign key.

CREATE TABLE hosts (
    id              SERIAL PRIMARY KEY,

    -- Human-readable name, e.g. "proxmox-node1", "web-vm-01", "sentinel-api-container"
    name            TEXT NOT NULL UNIQUE,

    -- What kind of resource this is. Kept as TEXT with a CHECK constraint
    -- (instead of a Postgres ENUM) so we can add new resource types later
    -- without a schema migration to alter an enum type.
    resource_type   TEXT NOT NULL CHECK (resource_type IN ('bare_metal', 'vm', 'lxc', 'docker')),

    -- Self-referencing FK: points to the id of the Host this one runs on.
    -- NULL for top-level resources (e.g. the bare-metal Proxmox node itself).
    parent_host_id  INTEGER REFERENCES hosts(id) ON DELETE SET NULL,

    -- When the agent last successfully reported in. NULL until first check-in.
    -- This is how we'll determine "is this host currently online" in Milestone 7/8.
    last_seen_at    TIMESTAMPTZ,

    -- When this host was first registered with Sentinel.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- metrics table
-- One row per individual metric reading (e.g. one row for "CPU: 42%",
-- another row for "Memory: 68%") rather than one row per host check-in
-- with a column per metric. This "narrow" format is the standard shape
-- for time-series data, and it's what lets us turn this into a
-- TimescaleDB hypertable below for efficient time-based storage/queries.

CREATE TABLE metrics (
    id              SERIAL,

    -- Which host this reading came from.
    host_id         INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,

    -- What kind of reading this is, e.g. 'cpu_percent', 'memory_percent',
    -- 'disk_percent', 'network_rx_bytes', 'network_tx_bytes'.
    -- Kept as TEXT (not ENUM) so new metric types don't need a migration.
    metric_type     TEXT NOT NULL,

    -- The actual reading. DOUBLE PRECISION covers percentages and byte
    -- counts alike without worrying about integer overflow or precision loss.
    value           DOUBLE PRECISION NOT NULL,

    -- When this reading was taken (not when it was inserted — the agent
    -- sets this, so a slow network doesn't skew the timestamp).
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Composite primary key required by TimescaleDB hypertables:
    -- the partitioning column (recorded_at) must be part of the key.
    PRIMARY KEY (id, recorded_at)
);

-- Turns the plain table above into a TimescaleDB "hypertable" —
-- this makes Postgres automatically partition the data into chunks
-- by time behind the scenes, which keeps queries and inserts fast
-- even once this table has millions of rows (this table will grow
-- the fastest of anything in Sentinel, since every host reports
-- multiple metrics on every check-in).
SELECT create_hypertable('metrics', by_range('recorded_at'));

-- Index to make "give me all CPU readings for host X over time" fast —
-- the most common query pattern for the dashboard's historical graphs.
CREATE INDEX idx_metrics_host_type_time ON metrics (host_id, metric_type, recorded_at DESC);

-- diagnostic_runs table
-- Stores the result of a single on-demand diagnostic action
-- (ping, traceroute, DNS lookup, port check, HTTP check) triggered
-- either manually from the dashboard or by an alert rule.

CREATE TABLE diagnostic_runs (
    id              SERIAL PRIMARY KEY,

    -- Which host ran this diagnostic (the agent that executed it).
    host_id         INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,

    -- Type of diagnostic: 'ping', 'traceroute', 'dns_lookup', 'port_check', 'http_check'.
    diagnostic_type TEXT NOT NULL CHECK (
        diagnostic_type IN ('ping', 'traceroute', 'dns_lookup', 'port_check', 'http_check')
    ),

    -- What was being tested, e.g. an IP, hostname, or URL depending on diagnostic_type.
    target          TEXT NOT NULL,

    -- Current state of this run — starts as 'pending' when requested via
    -- Redis pub/sub (Milestone 6), then updates to 'completed' or 'failed'
    -- once the agent finishes and reports back.
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'completed', 'failed')
    ),

    -- The actual result, shaped differently depending on diagnostic_type
    -- (e.g. traceroute has a list of hops, ping has latency/packet loss).
    -- JSONB instead of rigid columns because each diagnostic type's
    -- result shape is genuinely different, but we still want it
    -- queryable (unlike plain TEXT).
    result          JSONB,

    -- When this diagnostic was requested vs. when it actually finished.
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);

-- Speeds up "show me recent diagnostics for this host" on the dashboard.
CREATE INDEX idx_diagnostic_runs_host_time ON diagnostic_runs (host_id, requested_at DESC);

-- alert_rules table
-- A standing definition of a condition to watch for, e.g.
-- "alert if cpu_percent > 90 on host X". Milestone 7 evaluates
-- these rules against incoming metrics.

CREATE TABLE alert_rules (
    id              SERIAL PRIMARY KEY,

    -- Which host this rule applies to.
    host_id         INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,

    -- Which metric this rule watches, e.g. 'cpu_percent', 'memory_percent'.
    metric_type     TEXT NOT NULL,

    -- The comparison operator and threshold, e.g. operator='>' threshold=90.
    -- Kept as separate columns (not a raw expression string) so the
    -- evaluation logic in Milestone 7 doesn't need to parse arbitrary text.
    operator        TEXT NOT NULL CHECK (operator IN ('>', '<', '>=', '<=', '=')),
    threshold       DOUBLE PRECISION NOT NULL,

    -- Whether this rule is currently active. Lets you disable a rule
    -- without deleting it (and losing its alert history).
    enabled         BOOLEAN NOT NULL DEFAULT true,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- alert_events table
-- A specific instance of an alert_rule actually firing. One rule
-- can produce many events over time (e.g. CPU spikes on Monday,
-- then again on Friday — two separate events, same rule).

CREATE TABLE alert_events (
    id              SERIAL PRIMARY KEY,

    -- Which rule triggered this event.
    alert_rule_id   INTEGER NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,

    -- The actual metric value that triggered the rule, captured at
    -- fire-time (so you can see exactly what tripped it, even if
    -- the rule's threshold changes later).
    triggered_value DOUBLE PRECISION NOT NULL,

    -- Whether this alert has been acknowledged/resolved, or is still active.
    status          TEXT NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'resolved')
    ),

    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

-- Speeds up "show me alert history for this host" and
-- "show me all currently active alerts" on the dashboard.
CREATE INDEX idx_alert_rules_host ON alert_rules (host_id);
CREATE INDEX idx_alert_events_rule_time ON alert_events (alert_rule_id, triggered_at DESC);