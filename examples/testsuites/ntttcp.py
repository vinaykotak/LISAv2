from lisa import TestCaseMetadata, TestSuite, TestSuiteMetadata
from lisa.requirement import simple
from lisa.tools import Ntttcp


@TestSuiteMetadata(
    area="demo",
    category="two_node",
    description="""
    this is an example test suite.
    It helps to understand how test cases works on multiple nodes
    """,
    tags=["demo"],
    requirement=simple(min_node_count=2),
)
class NtttcpDemo(TestSuite):
    @TestCaseMetadata(
        description="""
        this test case send and receive data by ntttcp
        """,
        priority=1,
    )
    def send_receive(self) -> None:
        self._log.info(f"node count: {len(self.environment.nodes)}")
        server_node = self.environment.nodes[0]
        client_node = self.environment.nodes[1]

        ntttcp_server = server_node.tools[Ntttcp]
        ntttcp_client = client_node.tools[Ntttcp]

        server_process = ntttcp_server.run_async("-P 1 -t 5 -e")
        ntttcp_client.run(f"-s {server_node.internal_address} -P 1 -n 1 -t 5 -W 1")
        server_process.wait_result()
