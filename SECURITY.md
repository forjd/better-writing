# Security policy

Better Writing is prose instructions plus dependency-free Python scripts for validation and evals. It runs no service and stores no data, so the likely issues are narrow: a script that mishandles untrusted input, a CI workflow with too much access, or skill text that could steer an agent into unsafe actions.

## Reporting a vulnerability

Do not open a public issue. Open a [GitHub security advisory](https://github.com/forjd/better-writing/security/advisories/new) instead, so the report stays private until a fix is out.

Include what you found, the file or workflow involved, and steps to reproduce it.

## Supported versions

Only the latest release is supported. Fixes ship as a new release rather than backports.
