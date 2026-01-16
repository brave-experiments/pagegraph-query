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
