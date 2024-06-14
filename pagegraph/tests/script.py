from pagegraph.tests import PageGraphBaseTestClass


class ScriptCrossDomTestCase(PageGraphBaseTestClass):
    NAME = 'script_cross-dom'

    def test_par_domroots(self) -> None:
        html_nodes = self.graph.html_nodes()
        par_nodes = []
        for node in html_nodes:
            if node.tag_name() == "P":
                par_nodes.append(node)
        self.assertEqual(len(par_nodes), 1)

        par_node = par_nodes[0]
        creation_frame_id = par_node.domroot_for_creation().frame_id()
        document_frame_id = par_node.domroot_for_document().frame_id()
        self.assertNotEqual(creation_frame_id, document_frame_id)

        frame_id = par_node.domroot_for_serialization().frame_id()
        self.assertEqual(document_frame_id, frame_id)
