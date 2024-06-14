from pagegraph.tests import PageGraphBaseTestClass


ABOUT_BLANK_URL = "about:blank"
FRAME_URL = "/assets/blank-frame.html"


class IFramesBasicTestCase(PageGraphBaseTestClass):
    NAME = "iframes_about-blank"

    def test_num_iframes(self) -> None:
        frame_nodes = self.graph.iframe_nodes()
        self.assertEqual(len(frame_nodes), 1)

    def test_num_domroots(self) -> None:
        frame_nodes = self.graph.iframe_nodes()
        iframe_node = frame_nodes[0]
        domroot_nodes = iframe_node.domroot_nodes()
        self.assertEqual(len(domroot_nodes), 2)

        automatic_domroot = None
        final_domroot = None
        for domroot_node in domroot_nodes:
            if domroot_node.is_init_domroot():
                automatic_domroot = domroot_node
            else:
                final_domroot = domroot_node
        self.assertIsNotNone(automatic_domroot)
        self.assertEqual(automatic_domroot.url(), ABOUT_BLANK_URL)
        self.assertTrue(automatic_domroot.is_local_domroot())

        self.assertIsNotNone(final_domroot)
        self.assertEqual(final_domroot.url(), ABOUT_BLANK_URL)
        self.assertTrue(final_domroot.is_local_domroot())

        self.assertTrue(
            automatic_domroot.timestamp() <= final_domroot.timestamp())
        self.assertTrue(automatic_domroot.id() < final_domroot.id())


class IFramesNavigationTestCase(PageGraphBaseTestClass):
    NAME = "iframes_navigation"

    def test_num_iframes(self) -> None:
        frame_nodes = self.graph.iframe_nodes()
        self.assertEqual(len(frame_nodes), 1)

    def test_parser_generated_frame(self) -> None:
        frame_nodes = self.graph.iframe_nodes()
        iframe_node = frame_nodes[0]

        # There should be three child documents in the iframe:
        #  1. the initial about:blank frame
        #  2. the temporary about:blank one, created as part of the navigation
        #     process
        #  3. the navigated to "assets/blank-frame.html" frame.
        domroot_nodes = iframe_node.domroots()
        self.assertEqual(len(domroot_nodes), 3)

        init_domroot = None
        about_blank_domroot = None
        dest_domroot = None
        for node in domroot_nodes:
            if FRAME_URL in node.url():
                dest_domroot = node
            elif node.url() == ABOUT_BLANK_URL:
                if node.is_init_domroot():
                    init_domroot = node
                else:
                    about_blank_domroot = node
        self.assertIsNotNone(init_domroot)
        self.assertIsNotNone(about_blank_domroot)
        self.assertIsNotNone(dest_domroot)

        # Now check to make sure the nodes occurred in the expected order.
        self.assertTrue(
            init_domroot.timestamp() <= about_blank_domroot.timestamp())
        self.assertTrue(
            about_blank_domroot.timestamp() <= dest_domroot.timestamp())

        self.assertTrue(init_domroot.id() < about_blank_domroot.id())
        self.assertTrue(about_blank_domroot.id() < dest_domroot.id())


class IFramesNavigationTestCase(PageGraphBaseTestClass):
    NAME = "iframes_sub-document"

    def test_num_iframes(self) -> None:
        frame_nodes = self.graph.iframe_nodes()
        self.assertEqual(len(frame_nodes), 1)

    def test_text_frame_with_src(self) -> None:
        frame_nodes = self.graph.iframe_nodes()
        iframe_node = frame_nodes[0]

        domroot_nodes = iframe_node.domroot_nodes()
        self.assertEqual(len(domroot_nodes), 2)

        init_domroot = None
        dest_domroot = None
        for node in domroot_nodes:
            if ABOUT_BLANK_URL in node.url():
                init_domroot = node
            elif FRAME_URL in node.url():
                dest_domroot = node

        self.assertIsNotNone(init_domroot)
        self.assertIsNotNone(dest_domroot)
        self.assertTrue(init_domroot.timestamp() <= dest_domroot.timestamp())
        self.assertTrue(init_domroot.id() < dest_domroot.id())
