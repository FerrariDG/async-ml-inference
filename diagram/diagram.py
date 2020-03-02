from diagrams import Diagram
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import RabbitMQ
from diagrams.k8s.compute import Pod

graph_attr = {
    "pad": "0.2",
    "splines": "curved",
    "nodesep": "0.5",
    "ranksep": "1.0",
    "fontcolor": "#000000"
}

node_attr = {
    "fontsize": "15",
    "width": "1.2",
    "height": "1.2",
    "fontcolor": "#000000"
}


with Diagram(
    name="",
    show=False,
    filename="diagram/architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr={"color": "#566573"}
):

    client = Pod("Clients")

    api = Pod("APIs")

    broker = RabbitMQ("Broker")

    database = Redis("Database")

    worker = Pod("Workers")

    client << api << database << worker

    client >> api >> broker >> worker
