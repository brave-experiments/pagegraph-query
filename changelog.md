Version 0.6.5
---
Add ability to gate some functionality behind graph versions.

Report frame information for the `scripts` command if parsing graphs
versions 0.6.3 or later.


Version 0.6.4
---
Added two new commands: `elm` for querying information about a specific
graph element (and its surrounding subgraph), and `scripts` for querying
information about relationship chains between scripts on a page.


Version 0.6.3
---
Added graph structure type checks for edges.

Further cleaned up how reports are serialized.

Corrected handling of redirection flows for requests through the graph,
and exposed that information in the `RequestChainReport` structure
and the `requests` command.


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
