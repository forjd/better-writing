## sync

In this release, we added a powerful new `--since` flag to the `sync` command! This command is responsible for copying your remote records into the local cache, and now we handle incremental syncs seamlessly. It's worth noting that `--since` accepts an ISO 8601 date, such as `2026-09-01`, and if you leave it out, sync was changed to fetch the last 7 days by default.

We've also added `--dry-run`, which prints the records that would be copied without writing anything. Settings are read from `~/.config/acme/sync.toml`. If authentication fails, sync now exits with code 3.
