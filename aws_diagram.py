from diagrams import Diagram, Cluster
from diagrams.onprem.client import Users
from diagrams.onprem.network import Nginx
from diagrams.programming.language import Python

with Diagram("Django on EC2 with Nginx + uWSGI + SQLite3", show=False, outformat="png"):
    user = Users("Client")

    with Cluster("EC2 Instance"):
        nginx = Nginx("Nginx")
        uwsgi = Python("uWSGI + Django")
        sqlite = Python("SQLite3 (로컬 DB)")

        user >> nginx >> uwsgi >> sqlite