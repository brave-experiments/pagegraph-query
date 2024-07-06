usage: PageGraph Query [-h] [--version] [--debug]
                       {subframes,validate,requests,scripts,js-calls,elm} ...

Extracts information about a Web page's execution from a PageGraph recordings.

positional arguments:
  {subframes,validate,requests,scripts,js-calls,elm}
    subframes           Print information about subframes created and loaded
                        by page.
    validate            Just runs all validation and structure checks against
                        a graph.
    requests            Print information about requests made during page
                        execution.
    scripts             Print information about JS units executed during page
                        execution.
    js-calls            Print information about JS calls made during page
                        execution.
    elm                 Print information about a node or edge in the graph.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug
