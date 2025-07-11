Version 0.9.8
---
Fix error in `js-calls` command that caused JS invocations to be over counted.


Version 0.9.7
---
Fix situation where PageGraph would report a security origin as "null", but
pagegraph-query was expecting a `None` value.

For container DOM elements (`ParentDOMElementNode`), move fatal check for
attributes we see a delete record for, but no set record, to `validate()`,
and make `attributes()` ignore the unexpected situation case.


Version 0.9.6
---

Add support for [PageGraph 0.7.4](https://github.com/brave/brave-core/pull/28164),
changes, which explicitly includes frames' security origins in the
`DOMRootNode` object.

Related, add an additional `validation` step, to check that the security origin
recorded by PageGraph (and explicitly included in each graph file) matches
what we expect it to be based on graph structure. This serves as an additional
check to make sure that graph structures match the assumptions in
`pagegraph-query`.

Restructure how graphs for tests are generated, so that graphs for real-world
sites can be tested against too (in addition to the existing simple tests in
`pagegraph/tests/assets/html/*.html`).

Additional minor code cleanup, mostly removing more quotes around type
annotations, using `__future__.annotations`.

Upgrade mypy to 1.15.0.


---
Version 0.9.5
Add `url` into `ScriptLocal` summary for external scripts with new
`ScriptLocalNode.url_if_external` method.

Renamed `EventListenerEdge` to `EventListenerFiredEdge` to make it clearer
what the edge denotes.

Add `event_name` methods on `EventListenerAddEdge`, `EventListenerRemoveEdge`,
and `EventListenerEdge` edges.

Lots of cleanup (e.g., deleting a bunch of double quotes in annotations)
because of moving most everything to `from __future__ import annotations`.

Add ability for the event listener edges to look up where the event was
added, removed, or fired in the document with
`EventListenerEdge.event_add_edges()`, `EventListenerEdge.event_fired_edges()`,
and `EventListenerEdge.event_removed_edges()` methods.

Correctly handle when the URL for the top level frame is empty (which
should only happen for older graphs, generated with v0.7.2 and older).

Additional options for the `subframes` command, allowing for filtering frames
by first-and-third-party security origin.

Add ability to export subgraphs of the larger graph, using the `elm --graphml`
command in the `./run.py` script.

Additional test coverage.


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
