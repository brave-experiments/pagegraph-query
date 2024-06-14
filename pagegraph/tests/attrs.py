from pagegraph.graph.node import HTMLNode
from pagegraph.tests import PageGraphBaseTestClass


class AttributesBasicTestCase(PageGraphBaseTestClass):
    NAME = 'attrs_basic'

    def get_par_html_node(self) -> HTMLNode:
        par_html_node = None
        for html_node in self.graph.html_nodes():
            if html_node.tag_name() == "P":
                par_html_node = html_node
                break
        self.assertIsNotNone(par_html_node)
        assert par_html_node
        return par_html_node

    def test_set_attrs(self) -> None:
        par_html_node = self.get_par_html_node()

        attribute_set_edges = []
        for edge in par_html_node.incoming_edges():
            if attribute_set_edge := edge.as_attribute_set_edge():
                attribute_set_edges.append(attribute_set_edge)
        self.assertEqual(len(attribute_set_edges), 4)

        # First, check for the standard attribute set by the parser.
        std_parser_set_attr_set_edge = None
        non_std_parser_set_attr_set_edge = None
        method_set_attr_edge = None
        method_change_attr_edge = None
        for edge in attribute_set_edges:
            incoming_node = edge.incoming_node()
            if (edge.key() == "id" and
                    incoming_node.as_parser_node() is not None):
                std_parser_set_attr_set_edge = edge
            elif (edge.key() == "page-graph" and
                    incoming_node.as_parser_node() is not None):
                non_std_parser_set_attr_set_edge = edge
            elif (edge.key() == "hi" and
                    incoming_node.as_script_node() is not None):
                if edge.value() == "there":
                    method_set_attr_edge = edge
                elif edge.value() == "again":
                    method_change_attr_edge = edge
        self.assertIsNotNone(std_parser_set_attr_set_edge)
        self.assertEqual(std_parser_set_attr_set_edge.value(), "my-par")

        self.assertIsNotNone(non_std_parser_set_attr_set_edge)
        self.assertEqual(non_std_parser_set_attr_set_edge.value(), "test")

        self.assertIsNotNone(method_set_attr_edge)
        self.assertIsNotNone(method_change_attr_edge)

    def test_del_attrs(self) -> None:
        par_html_node = self.get_par_html_node()

        attribute_delete_edges = []
        for edge in par_html_node.incoming_edges():
            if attribute_delete_edge := edge.as_attribute_delete_edge():
                attribute_delete_edges.append(attribute_delete_edge)
        self.assertEqual(len(attribute_delete_edges), 1)

        attr_delete_edge = attribute_delete_edges[0]
        self.assertIsNotNone(attr_delete_edge.incoming_node().as_script_node())
        self.assertEqual(attr_delete_edge.key(), "id")
