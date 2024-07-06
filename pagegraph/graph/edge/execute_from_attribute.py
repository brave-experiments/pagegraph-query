from pagegraph.graph.edge.execute import ExecuteEdge


class ExecuteFromAttributeEdge(ExecuteEdge):

    incoming_node_type_names = [
        "HTML element",  # Node.Types.HTML_NODE
    ]

    outgoing_node_type_names = [
        "script",  # Node.Types.SCRIPT
    ]
