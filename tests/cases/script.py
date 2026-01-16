from __future__ import annotations

from tests.cases.abc.base import PageGraphBaseTestClass


# pylint: disable=too-few-public-methods
class ScriptCrossDomTestCase(PageGraphBaseTestClass):
    NAME = "gen/script-cross_dom"

    def test_par_domroots(self) -> None:
        html_nodes = self.graph.html_nodes()
        par_nodes = []
        for node in html_nodes:
            if node.tag_name() == "P":
                par_nodes.append(node)
        self.assertEqual(len(par_nodes), 1)

        par_node = par_nodes[0]
        assert par_node

        domroot_for_creation = par_node.domroot_for_creation()
        assert domroot_for_creation
        creation_frame_id = domroot_for_creation.frame_id()

        domroot_for_document = par_node.domroot_for_document()
        assert domroot_for_document
        document_frame_id = domroot_for_document.frame_id()

        self.assertNotEqual(creation_frame_id, document_frame_id)

        domroot_for_serialization = par_node.domroot_for_serialization()
        assert domroot_for_serialization
        frame_id = domroot_for_serialization.frame_id()
        self.assertEqual(document_frame_id, frame_id)


# pylint: disable=too-few-public-methods
class ScriptJsCallsTestCase(PageGraphBaseTestClass):
    NAME = "gen/script-js_calls"

    def test_num_scripts(self) -> None:
        child_frame_url = "assets/frames/script_js-calls_child_frame.html"
        main_domroot = None
        for node in self.graph.toplevel_domroot_nodes():
            if "script-js_calls" in str(node.url()):
                main_domroot = node
                break

        assert main_domroot
        child_domroots = main_domroot.domroot_nodes(func=lambda x: child_frame_url in str(x.url()))
        self.assertEqual(len(child_domroots), 1)

        raw_main_frame_scripts = main_domroot.scripts_executed_from()
        main_frame_scripts = self.filter_nodes(raw_main_frame_scripts)
        self.assertEqual(len(main_frame_scripts), 4)

        child_domroot = child_domroots[0]
        raw_frame_scripts = child_domroot.scripts_executed_from()
        frame_scripts = self.filter_nodes(raw_frame_scripts)
        self.assertEqual(len(frame_scripts), 1)

        all_scripts = list(main_frame_scripts) + list(frame_scripts)
        attr_sets = set()
        for script in all_scripts:
            script_local_node = script.as_script_local_node()
            self.assertIsNotNone(script_local_node)
            assert script_local_node
            for js_call_result in script_local_node.calls("Performance.now"):
                attr_sets.add(js_call_result.pretty_print())
        self.assertEqual(len(attr_sets), 5)

class ScriptNumJsCallsTestCase(PageGraphBaseTestClass):
    NAME = "gen/script-num-js_calls"

    def test_num_js_calls(self) -> None:
        js_structure_nodes = self.graph.js_structure_nodes()
        for js_node in js_structure_nodes:
            results = js_node.call_results()
            self.assertEqual(len(results), 2)
