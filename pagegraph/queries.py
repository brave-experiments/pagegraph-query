import networkx as NWX

import pagegraph.utils as PG_U


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
        for _, edge_data in edge_info.items():
            if edge_data['edge type'] != "execute":
                continue
            return parent_nid
    PG_U.throw_node_related_error(
        graph, nid, f"Can't find execution edge for nid={nid}")


def nid_of_parser_for_frame_containing_script_node(graph, nid):
    node_data = graph.nodes[nid]

    reverse_graph = NWX.reverse_view(graph)
    parent_nodes = reverse_graph.adj[nid]

    if node_data["node type"] != "script":
        PG_U.throw_node_related_error(
            graph, nid, f"Expected a script node for nid={nid}")

    target_parent_node_type = None
    if node_data["script type"] == "inline inside generated element":
        target_parent_node_type = "HTML element"
    else:
        target_parent_node_type = "script"

    for parent_nid, edge_info in parent_nodes.items():
        for _, edge_data in edge_info.items():
            if edge_data["edge type"] != "execute":
                continue
            parent_node_data = graph.nodes[parent_nid]
            if parent_node_data["node type"] == target_parent_node_type:
                return nid_of_parser_for_frame_containing_node(
                    graph, parent_nid)
    PG_U.throw_node_related_error(
        graph, nid, f"Can't find a path to the parser script node nid={nid}")


def nid_of_parser_for_frame_containing_node(graph, nid):
    node_data = graph.nodes[nid]
    if node_data["node type"] == "script":
        return nid_of_parser_for_frame_containing_script_node(graph, nid)

    reverse_graph = NWX.reverse_view(graph)
    parent_nodes = reverse_graph.adj[nid]
    for parent_nid, edge_info in parent_nodes.items():
        for _, edge_data in edge_info.items():
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
    PG_U.throw_node_related_error(
        graph, nid, f"Couldn't find a path to the parser for nid={nid}")


def nids_of_docroots_for_parser(graph, nid):
    dom_root_nids = []
    for child_nid, _ in graph.adj[nid].items():
        if graph.nodes[child_nid]['node type'] == "DOM root":
            dom_root_nids.append(child_nid)
    if len(dom_root_nids) == 0:
        PG_U.throw_node_related_error(
            graph, nid, f"Found no DOM roots for parser nid={nid}")
    return dom_root_nids


def nid_of_docroot_containing_node(graph, nid):
    """We cheat here by finding the docroot node that has an id closest to, but
    not larger than, the given node (since any document with a higher pg id
    had to be created after this node, and so could not contain the given
    node)."""
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
        for _, edge_data in edge_info.items():
            if edge_data['edge type'] != "cross DOM":
                continue
            child_frame_parser_nid = child_nid
            return nids_of_docroots_for_parser(graph, child_frame_parser_nid)
    PG_U.throw_node_related_error(
        graph, nid, f"Found no DOC Roots for nid={nid}")


def summarize_iframe(graph, nid):
    parent_docroot_nid = nid_of_docroot_containing_node(graph, nid)
    parent_docroot_url = url_for_docroot(graph, parent_docroot_nid)

    child_docroot_nids = nids_of_docroots_for_iframe(graph, nid)
    child_docroots = [
        (a_nid, url_for_docroot(graph, a_nid)) for a_nid in child_docroot_nids]
    child_docroots_sorted = sorted(
        child_docroots, key=lambda x: _pg_id(graph, x[0]))
    docroot_dicts = [{"nid": x[0], "url": x[1]} for x in child_docroots_sorted]

    return {
        "parent frame": {
            "nid": parent_docroot_nid,
            "url": parent_docroot_url
        },
        "child documents": docroot_dicts
    }


def summarize_iframes_in_graph(graph, only_local=False):
    iframe_nids = nids_of_iframes(graph)
    summaries = [summarize_iframe(graph, a_nid) for a_nid in iframe_nids]
    if not only_local:
        return summaries
    local_frame_summaries = []
    for summary in summaries:
        if summary["child documents"][-1]["url"] == "about:blank":
            local_frame_summaries.append(summary)
    return local_frame_summaries
