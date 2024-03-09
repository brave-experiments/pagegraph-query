import networkx as NWX


def _pg_id(graph, nid):
    return int(graph.nodes[nid]['id'])


def nids_of_iframes(graph):
    iframe_nids = []
    for n in graph.nodes(data=True):
        if n[1]['node type'] == 'frame owner' and n[1]['tag name'] == 'IFRAME':
            iframe_nids.append(n[0])
    return iframe_nids


def nid_of_html_node_for_script_node(graph, nid):
    reverse_graph = NWX.reverse_view(graph)
    for parent_nid, edge_info in reverse_graph.adj[nid].items():
        for edge_id, edge_data in edge_info.items():
            if edge_data['edge type'] != "execute":
                continue
            return parent_nid
    raise Exception(nid, "Couldn't find execution edge for nid")


def nid_of_parser_for_frame_containing_node(graph, nid):
    reverse_graph = NWX.reverse_view(graph)
    parent_nodes = reverse_graph.adj[nid]

    for parent_nid, edge_info in parent_nodes.items():
        for edge_id, edge_data in edge_info.items():
            if edge_data["edge type"] != "create node":
                continue
            parent_node_data = graph.nodes[parent_nid]
            if parent_node_data["node type"] == "parser":
                return parent_nid
            if parent_node_data["node type"] == "script":
                script_elm_nid = nid_of_html_node_for_script_node(
                    graph, parent_nid)
                return nid_of_parser_for_frame_containing_node(
                    graph, script_elm_nid)
    raise Exception(nid, "Couldn't find a path to the parser for nid")


def nids_of_docroots_for_parser(graph, nid):
    dom_root_nids = []
    for child_nid, edge_info in graph.adj[nid].items():
        if graph.nodes[child_nid]['node type'] == "DOM root":
            dom_root_nids.append(child_nid)
    if len(dom_root_nids) == 0:
        raise Exception(nid, "Found no DOM roots for parser")
    return dom_root_nids


def nid_of_docroot_containing_node(graph, nid):
    """We cheat here by finding the docroot node that has an id closest to, but
    not larger than, the given node (since any document with a higher pg id)
    had to be created after this node, and so could not contain the given
    node."""
    node_pg_id = _pg_id(graph, nid)

    parser_nid = nid_of_parser_for_frame_containing_node(graph, nid)
    docroot_nids = nids_of_docroots_for_parser(graph, parser_nid)
    dr_nids_pgids = [(a_nid, _pg_id(graph, a_nid)) for a_nid in docroot_nids]
    dr_nids_pgids_sorted = sorted(dr_nids_pgids, key=lambda x: x[1])

    # The list now contains (docroot_nid, docroot_pgid), from last created
    # to earliest created.
    dr_nids_pgids_sorted.reverse()
    for docroot_nid, docroot_pgid in dr_nids_pgids_sorted:
        if docroot_pgid > node_pg_id:
            continue
        return docroot_nid


def url_for_docroot(graph, nid):
    return graph.nodes[nid]["url"]


def nids_of_docroots_for_iframe(graph, nid):
    for child_nid, edge_info in graph.adj[nid].items():
        for edge_id, edge_data in edge_info.items():
            if edge_data['edge type'] != "cross DOM":
                continue
            child_frame_parser_nid = child_nid
            return nids_of_docroots_for_parser(graph, child_frame_parser_nid)
    raise Exception(nid, "Found no DOC Roots")


def summarize_iframe(graph, nid):
    parent_docroot_nid = nid_of_docroot_containing_node(graph, nid)
    parent_docroot_url = url_for_docroot(graph, parent_docroot_nid)

    child_docroot_nids = nids_of_docroots_for_iframe(graph, nid)
    child_docroots = [
        (a_nid, url_for_docroot(graph, a_nid)) for a_nid in child_docroot_nids]
    child_docroots_sorted = sorted(
        child_docroots, key=lambda x: _pg_id(graph, x[0]))

    return {
        "parent frame": {
            "nid": parent_docroot_nid,
            "url": parent_docroot_url
        },
        "child documents": child_docroots_sorted
    }


def summarize_iframes_in_graph(graph):
    iframe_nids = nids_of_iframes(graph)
    return [summarize_iframe(graph, frame_nid) for frame_nid in iframe_nids]
