## sync

`sync` copies remote records into the local cache. It syncs incrementally.

`--since` takes an ISO 8601 date, such as `2026-09-01`, and copies only records changed on or after it. Without it, `sync` fetches the last 7 days.

`--dry-run` prints the records that would be copied without writing anything.

Settings are read from `~/.config/acme/sync.toml`. If authentication fails, `sync` exits with code 3.
