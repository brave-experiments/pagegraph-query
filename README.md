PageGraph-Query
===

This is a library and commandline tool designed to simplify querying and
working with the [Brave](https://brave.com)
[PageGraph](https://github.com/brave/brave-browser/wiki/PageGraph) system.
PageGraph records information about a broad range of events and
actions that occur when Blink and Chromium are executing a website.

What is PageGraph
---

Importantly, this information is **attributed**, meaning that not only
will PageGraph record events like "a `<section>` element was inserted into the
document" or "a request for an image was made" or "the value 4 was stored
as the value `counter` in `localStorage`", but (importantly) what in the page
caused that event to happen (so, "the HTML parser inserted a `<section>` element
into the page", "this particular `<img>` element requested for an image," or
"this specific script stored the value in `localStorage`).

This is similar to the `initiator` column in Chromium's developer tools
interface, but 1. for **every** action and event that happened during a
page's execution, 2. serialized in a graph format that enables after-the-fact
measurements and investigations, and 3. with an even higher level of
accuracy.

PageGraph has three parts:
- [patches and additions](https://sourcegraph.com/github.com/brave/brave-core/-/tree/third_party/blink/renderer/core/brave_page_graph) to the version of Blink included in desktop and
  Android versions of the Brave Browser.
- [pagegraph-crawl](https://github.com/brave/pagegraph-crawl), a node program
  for crawling pages in PageGraph and recording the output as GraphML format
  XML files, and
- [pagegraph-query](https://github.com/brave-experiments/pagegraph-query),
   this tool, for querying and asking questions of the resulting PageGraph
   recordings.

Using PageGraph-Query
---

This main way to use this tool is from the commandline, through the included
`pagegraph-query` command (or the included `run.py` script). Different
kinds of queries are wrapped up as subcommands. You can find more information
about each of these queries using `--help`.

```
usage: PageGraph Query [-h] [--version] [--debug]
                       {elm,html,js-calls,requests,scripts,subframes,unknown,validate} ...

Extracts information about a Web page's execution from a PageGraph recordings.

positional arguments:
  {elm,html,js-calls,requests,scripts,subframes,unknown,validate}
    elm                 Print information about a node or edge in the graph.
    html                Print information about the HTML elements in a
                        document.
    js-calls            Print information about JS calls made during page
                        execution.
    requests            Print information about requests made during
                        execution.
    scripts             Print information about JS execution during page
                        execution.
    subframes           Print information about subframes created by page.
    unknown             Print information about any events that occurred where
                        we could not attribute the script event to a running
                        script. (note this is different from the 'validate'
                        command, which only checks if the structure of the
                        graph is as expected).
    validate            Runs all validation and structure checks against a
                        graph.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug
```