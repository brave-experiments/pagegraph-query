from pagegraph.tests import PageGraphBaseTestClass
from pagegraph.graph.node.script_local import ScriptLocalNode


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

    def setUp(self):
        super().setUp()
        child_frame_url = "assets/frames/script_js-calls_child_frame.html"
        main_domroot = None
        toplevel_domroot_nodes = self.graph.toplevel_domroot_nodes()
        for node in toplevel_domroot_nodes:
            if "script-js_calls" in str(node.url()):
                main_domroot = node
                break

        assert main_domroot
        child_domroots = main_domroot.domroot_nodes(func=lambda x: child_frame_url in str(x.url()))
        self.assertEqual(len(child_domroots), 1)

        child_domroot = child_domroots[0]

        raw_main_frame_scripts = main_domroot.scripts_executed_from()
        self.main_frame_scripts = self.filter_nodes(raw_main_frame_scripts)

        raw_frame_scripts = child_domroot.scripts_executed_from()
        self.frame_scripts = self.filter_nodes(raw_frame_scripts)

        self.all_scripts = self.main_frame_scripts + self.frame_scripts

    def test_num_scripts(self) -> None:
        self.assertEqual(len(self.main_frame_scripts), 9)
        self.assertEqual(len(self.frame_scripts), 1)
        attr_sets = set()
        for script in self.all_scripts:
            for js_call_result in script.calls("Performance.now"):
                attr_sets.add(js_call_result.pretty_print())
        self.assertEqual(len(attr_sets), 9)

    def test_script_texts(self) -> None:
        expected_texts = [
            "inline::",
            "module4::",
            "childframe::",
            "import('/assets/js/script_js-module-1.js')"
        ]

        actual_texts = [
            script.matching_text_node().text()
            for script in self.all_scripts
            if script.matching_text_node()
        ]

        self.assertEqual(len(actual_texts), len(expected_texts))
        for expected in expected_texts:
            assert any(expected in actual for actual in actual_texts), \
            f"Expected text '{expected}' not found in actual texts"

    def test_script_urls(self) -> None:
        excepted_urls = [
            "http://[::]:8000/assets/js/script_js-module-1.js",
            "http://[::]:8000/assets/js/script_js-module-2.js",
            "http://[::]:8000/assets/js/script_js-module-3.js",
            "http://[::]:8000/assets/js/script_js-calls_async.js",
            "http://[::]:8000/assets/js/script_js-calls_standard.js",
        ]

        actual_urls = [
            script.url_if_available()
            for script in self.all_scripts
            if script.script_type() in ScriptLocalNode.script_types_potentially_with_urls
            and script.url_if_available() is not None
        ]

        self.assertEqual(sorted(excepted_urls), sorted(actual_urls))


class ScriptNumJsCallsTestCase(PageGraphBaseTestClass):
    NAME = "gen/script-num-js_calls"

    def test_num_js_calls(self) -> None:
        js_structure_nodes = self.graph.js_structure_nodes()
        for js_node in js_structure_nodes:
            results = js_node.call_results()
            self.assertEqual(len(results), 2)
