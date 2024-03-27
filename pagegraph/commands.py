import pagegraph.graph


def frametree(input_path):
    pg = pagegraph.graph.from_path(input_path)
    toplevel_domroot_nodes = pg.toplevel_domroot_nodes()

    trees = []
    for domroot_node in toplevel_domroot_nodes:
        summary = {
            "url": domroot_node.url(),
            "nid": domroot_node.id()
        }

        tree_for_docroot = pg.summarize_docroot_frametree(docroot_nid)
        trees.append(tree_for_docroot)
    return trees


def subframes(input_path, local_only=False):
    pg = pagegraph.graph.from_path(input_path)
    summaries = []

    for iframe_node in pg.iframe_nodes():
        iframe_summary = {}
        parent_frame = iframe_node.domroot()
        parent_frame_url = parent_frame.url()
        parent_frame_nid = parent_frame.id()
        iframe_summary["parent frame"] = {
            "url": parent_frame_url,
            "nid": parent_frame_nid
        }
        iframe_summary["iframe"] = {
            "nid": iframe_node.id()
        }

        child_documents = []
        for domroot_node in iframe_node.child_domroots():
            child_documents.append({
                "nid": domroot_node.id(),
                "url": domroot_node.url()
            })
        iframe_summary["child documents"] = child_documents
        summaries.append(iframe_summary)
    return summaries

    # summaries = [pg.summarize_iframe(a_nid) for a_nid in iframe_nids]
    # if local_only:
    #     return summaries
    # local_frame_summaries = []
    # for summary in summaries:
    #     if summary["child documents"][-1]["url"] == "about:blank":
    #         local_frame_summaries.append(summary)
    # return local_frame_summaries


def requests(input_path, frame_nid=None):
    pg = PG_G.from_path(input_path)

    # if frame_nid and not PG_V.is_node_of_type(graph, frame_nid, "DOM root"):
    #     raise ValueError(f"{frame_nid} is not a node of type 'DOM root'")

    docroot_nids = pg.nids_of_all_docroots()
    print("docroot nids")
    print(docroot_nids)

    print(f"docroot_nids[0]={docroot_nids[0]}")
    return pg.nids_of_nodes_in_docroot(docroot_nids[0])
