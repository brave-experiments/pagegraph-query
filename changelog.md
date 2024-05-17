Version 0.6.2
---
Add new `js-calls` query command, to allow querying what JS calls were
made during page execution.

Rework how JSON reports are defined and implemented, to allow it to
be `mypy` checked, and to make the reports more consistent.

Much faster.

Version 0.6.1
---
Add explicitly passed `--debug` option on command line, to optionally
perform more expensive checks of graph correctness. Started moving
`assert`s to this, to give more useful failure information.

Correct assertions in code about resource nodes and connected request
edges to incorporate new request redirect edges.
