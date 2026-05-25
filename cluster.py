from cassandra.cluster import Cluster, NoHostAvailable, Session


def connect_to_cluster(
    ip_addrs: list = ["127.0.0.1", "127.0.0.2", "127.0.0.3"],
    port: int = 9042
) -> Session:
    session = None
    try:
        cluster = Cluster(ip_addrs, port=port)
        session = cluster.connect()
    except NoHostAvailable as e:
        print(f"No hosts available to connect to the Cassandra cluster: {e}")
        exit(1)
    except Exception as e:
        print(f"Error connecting to Cassandra cluster: {e}")
        exit(1)

    assert session is not None, (
        "Failed to establish a session with the Cassandra cluster."
    )

    return session
