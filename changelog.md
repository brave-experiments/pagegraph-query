Version 0.9.4
---

Add support for PageGraph version 0.7.2 (which adds new node types for actors).

Fix `iframes` test and regenerate test graphs with recent pagegraph.

Add additional tests for keeping track of js calls across frames.

Add additional command for logging if any unattributable events occurred
in the graph (i.e., cases where there must have been a script occurring, but
we couldn't determine which script.).

Fix issue with deeply recursive request loops (specifically, when the
same URL could redirect to itself a large but finite number of times, before
redirecting to an eventual end URL).

Move all abstract node and edge classes into `pagegraph.graph.{node,edge}.abc`
so that the directory structure more closely matches the PageGraph type
taxonomy.

Remove assumption in `RequestChain` class that all requests will have a result
(either a completion edge or an error edge). There will be no result if the
graph was serialized while the request was still in the air.


Version 0.9.3
---

Fix frame filter for `requests` command.


Version 0.9.2
---

Add `html` command, for querying what HTML elements appeared in which pages.

Made some minor changes to get python 3.10 compatibility


Version 0.9.1
---

Add some tests.

Moved to pylint linting, which required a lot of code restructuring.

Parse headers in relevant requests.


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
