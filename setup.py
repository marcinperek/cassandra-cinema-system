from uuid import uuid4

from cluster import connect_to_cluster


def setup():
    session = connect_to_cluster()

    try:
        session.execute(
            "CREATE KEYSPACE IF NOT EXISTS cinema WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}",
            timeout=20,
        )
    except Exception as e:
        print(f"Error creating keyspace: {e}")
        exit(1)

    session.set_keyspace("cinema")
    try:
        session.execute("DROP TABLE IF EXISTS movies;", timeout=20)
        session.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                screening_id UUID,
                movie_title text,
                screening_time timestamp,
                room_number int,
                total_seats int,
                PRIMARY KEY (screening_id)
            )
            """,
            timeout=20,
        )
    except Exception as e:
        print(f"Error creating table movies: {e}")
        exit(1)

    try:
        session.execute("DROP TABLE IF EXISTS reservations;", timeout=20)
        session.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                screening_id UUID,
                seat_number int,
                reservation_id UUID,
                movie_title text,
                screening_time timestamp,
                user_name text,
                user_email text,
                PRIMARY KEY (screening_id, seat_number)
            )
            """,
            timeout=20,
        )
    except Exception as e:
        print(f"Error creating table reservations: {e}")
        exit(1)

    try:
        session.execute("DROP TABLE IF EXISTS reservations_by_user;", timeout=20)
        session.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations_by_user (
                user_email text,
                reservation_id UUID,
                user_name text,
                screening_id UUID,
                seat_number int,
                movie_title text,
                screening_time timestamp,
                PRIMARY KEY (user_email, reservation_id)
            )
            """,
            timeout=20,
        )
    except Exception as e:
        print(f"Error creating table reservations_by_users {e}")
        exit(1)

    try:
        movies = [
            {
                "screening_id": uuid4(),
                "movie_title": "Inception",
                "screening_time": "2026-05-27 19:00:00",
                "room_number": 1,
                "total_seats": 100,
            },
            {
                "screening_id": uuid4(),
                "movie_title": "The Matrix",
                "screening_time": "2026-05-27 21:00:00",
                "room_number": 2,
                "total_seats": 80,
            },
        ]
        for movie in movies:
            session.execute(
                "INSERT INTO movies (screening_id, movie_title, screening_time, room_number, total_seats) VALUES (%s, %s, %s, %s, %s);",
                (
                    movie["screening_id"],
                    movie["movie_title"],
                    movie["screening_time"],
                    movie["room_number"],
                    movie["total_seats"],
                ),
                timeout=20,
            )

    except Exception as e:
        print(f"Error inserting movies: {e}")
        exit(1)


if __name__ == "__main__":
    setup()
