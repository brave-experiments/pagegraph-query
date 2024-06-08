from pagegraph.tests import PageGraphBaseTestClass


class IFrameBasicTestCase(PageGraphBaseTestClass):
    NAME = 'iframe:basic'

    def test_num_frames(self) -> None:
        frame_nodes = self.graph.iframe_nodes()
        self.assertEqual(len(frame_nodes), 1)

    def test_num_domroots_in_frame(self) -> None:
        iframe_node = self.graph.iframe_nodes()[0]

        domroot_nodes = iframe_node.domroots()
        self.assertEqual(len(domroot_nodes), 2)

        domroot_urls = set([x.url() for x in domroot_nodes])
        self.assertTrue("about:blank" in domroot_urls)

        domroot_urls.remove("about:blank")
        other_url = domroot_urls.pop()
        assert other_url
        self.assertTrue(other_url.endswith("blank-frame.html"))
