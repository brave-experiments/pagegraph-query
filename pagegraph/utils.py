import sys


def describe_node(graph, nid) -> str:
    node = graph.nodes[nid]
    output = f"node nid={nid}\n"
    for attr_name, attr_value in node.items():
        output += f"- {attr_name}={str(attr_value).replace("\n", "\\n")}\n"
    return output


def throw_node_related_error(graph, nid, desc):
    node_desc = describe_node(graph, nid)
    sys.stderr.write("Unexpected case when handling a node")
    sys.stderr.write(node_desc)
    sys.stderr.write("\n")
    raise Exception(desc)
