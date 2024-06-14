from pagegraph.graph.edge import Edge
from pagegraph.tests import PageGraphBaseTestClass


class LocalStorageBasicTestCase(PageGraphBaseTestClass):
    NAME = 'localstorage_basic'

    def test_storage_set(self) -> None:
        storage_set_edges = self.graph.storage_set_edges()
        self.assertEqual(len(storage_set_edges), 2)

        found_test_set = False
        found_other_set = False
        for edge in storage_set_edges:
            script_node = edge.incoming_node().as_script_node()
            self.assertIsNotNone(script_node)

            local_storage_node = edge.outgoing_node().as_local_storage_node()
            self.assertIsNotNone(local_storage_node)
            edge_key = edge.key()
            edge_value = edge.value()
            if edge.key() == "test" and edge.value() == "\"value\"":
                found_test_set = True
            elif edge.key() == "other" and edge.value() == "\"newer\"":
                found_other_set = True

        self.assertTrue(found_test_set)
        self.assertTrue(found_other_set)

    def test_storage_delete(self) -> None:
        storage_delete_edges = self.graph.storage_delete_edges()
        self.assertEqual(len(storage_delete_edges), 1)
        storage_delete_edge = storage_delete_edges[0]

        self.assertIsNotNone(
            storage_delete_edge.incoming_node().as_script_node())
        self.assertIsNotNone(
            storage_delete_edge.outgoing_node().as_local_storage_node())
        self.assertEqual(storage_delete_edge.key(), "test")

    def test_storage_clear(self) -> None:
        storage_clear_edges = self.graph.storage_clear_edges()
        self.assertEqual(len(storage_clear_edges), 1)
        storage_clear_edge = storage_clear_edges[0]

        self.assertIsNotNone(
            storage_clear_edge.incoming_node().as_script_node())
        self.assertIsNotNone(
            storage_clear_edge.outgoing_node().as_local_storage_node())


class LocalStorageCrossFrameTestCase(PageGraphBaseTestClass):
    NAME = 'localstorage_cross-frame'

    def test_storage_set(self) -> None:
        storage_set_edges = self.graph.storage_set_edges()
        self.assertEqual(len(storage_set_edges), 2)

        top_domroots = self.graph.toplevel_domroot_nodes()
        toplevel_frame_ids = [x.frame_id() for x in top_domroots]

        iframe_elm = self.graph.iframe_nodes()[0]
        child_domroots = iframe_elm.domroot_nodes()
        child_frame_ids = [x.frame_id() for x in child_domroots]

        parent_frame_edge = None
        child_frame_edge = None
        for edge in storage_set_edges:
            self.assertIsNotNone(edge.incoming_node().as_script_node())
            self.assertIsNotNone(edge.outgoing_node().as_local_storage_node())
            if edge.value() == "\"top\"":
                parent_frame_edge = edge
            elif edge.value() == "\"child\"":
                child_frame_edge = edge

        self.assertIsNotNone(parent_frame_edge)
        self.assertIsNotNone(child_frame_edge)

        self.assertTrue(parent_frame_edge.frame_id() in toplevel_frame_ids)
        self.assertTrue(child_frame_edge.frame_id() in child_frame_ids)
