from __future__ import annotations

from pagegraph.graph.node.html import HTMLNode
from pagegraph.tests import PageGraphBaseTestClass


class AttributesBasicTestCase(PageGraphBaseTestClass):
    NAME = "gen/attrs-basic"

    def get_par_html_node(self) -> HTMLNode:
        par_html_node = None
        for html_node in self.graph.html_nodes():
            if html_node.tag_name() == "P":
                par_html_node = html_node
                break
        self.assertIsNotNone(par_html_node)
        assert par_html_node
        return par_html_node

    def test_get_element_by_id(self) -> None:
        # This should be None, bc the element's id was deleted
        # during the page's execution
        self.assertEqual(len(self.graph.get_elements_by_id("my-par")), 0)
        self.assertEqual(len(self.graph.get_elements_by_id_ever("my-par")), 1)

    def test_attributes(self) -> None:
        par_node = self.get_par_html_node()
        self.assertEqual(par_node.get_attribute("hi"), "again")

    def test_attributes_ever(self) -> None:
        par_node = self.get_par_html_node()
        all_hi_values = par_node.get_attribute_ever("hi")
        self.assertIn("there", all_hi_values)
        self.assertIn("again", all_hi_values)

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
                    incoming_node.as_script_local_node() is not None):
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
        acting_script = attr_delete_edge.incoming_node().as_script_local_node()
        self.assertIsNotNone(acting_script)
        self.assertEqual(attr_delete_edge.key(), "id")
