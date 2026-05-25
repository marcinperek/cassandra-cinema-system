import tornado
import asyncio
import json
from cluster import connect_to_cluster
from cassandra.cluster import BatchStatement
from uuid import uuid4, UUID


select_reservations_by_screening = "SELECT * FROM reservations WHERE screening_id=%s;"
select_reservations_by_email = "SELECT * FROM reservations_by_user WHERE user_email=%s;"
select_movies = "SELECT * FROM movies;"
select_movie_by_screening = "SELECT * FROM movies WHERE screening_id=%s;"
add_reservation = "INSERT INTO reservations (screening_id, seat_number, reservation_id, movie_title, screening_time, user_name, user_email) VALUES (%s, %s, %s, %s, %s, %s, %s) IF NOT EXISTS;"
add_reservation_user = "INSERT INTO reservations_by_user (user_email, reservation_id, user_name, screening_id, seat_number, movie_title, screening_time) VALUES (%s, %s, %s, %s, %s, %s, %s);"
update_reservation = (
    "UPDATE reservations SET user_name=%s WHERE screening_id=%s AND seat_number=%s;"
)
update_reservation_user = "UPDATE reservations_by_user SET user_name=%s WHERE user_email=%s AND reservation_id=%s;"


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        user_email = self.get_argument("user_email", default=None)
        screening_id = self.get_argument("screening_id", default=None)

        if user_email is not None:
            res = session.execute(select_reservations_by_email, (user_email,))
            if res is None:
                self.set_status(500)
                self.write(json.dumps({"error": "Failed to fetch reservations"}))
                return
            if res.one() is None:
                self.set_status(404)
                self.write(
                    json.dumps({"error": "No reservations found for this email"})
                )
                return

            user_reservations = {
                "user_reservations": [
                    {
                        "screening_id": str(row.screening_id),
                        "reservation_id": str(row.reservation_id),
                        "title": row.movie_title,
                        "time": row.screening_time.isoformat(),
                        "seat": row.seat_number,
                        "user_name": row.user_name,
                        "user_email": row.user_email,
                    }
                    for row in res
                ],
                "error": None,
            }
            self.write(json.dumps(user_reservations))

        elif screening_id is not None:
            res = session.execute(
                select_reservations_by_screening, (UUID(screening_id),)
            )
            if res is None:
                self.set_status(500)
                self.write(json.dumps({"error": "Failed to fetch reservations"}))
                return
            if res.one() is None:
                self.set_status(404)
                self.write(
                    json.dumps({"error": "No reservations found for this screening"})
                )
                return

            movie_reservations = {
                "movie_reservations": [
                    {
                        "screening_id": str(row.screening_id),
                        "reservation_id": str(row.reservation_id),
                        "title": row.movie_title,
                        "time": row.screening_time.isoformat(),
                        "seat": row.seat_number,
                        "user_name": row.user_name,
                        "user_email": row.user_email,
                    }
                    for row in res
                ],
                "error": None,
            }
            self.write(json.dumps(movie_reservations))

        else:
            res = session.execute(select_movies)
            if res is None:
                self.set_status(500)
                self.write(json.dumps({"error": "Failed to fetch movies"}))
                return

            movie_list = {
                "movie_list": [
                    {
                        "title": row.movie_title,
                        "time": row.screening_time.isoformat(),
                        "screening_id": str(row.screening_id),
                        "room": row.room_number,
                    }
                    for row in res
                ],
                "error": None,
            }
            self.write(json.dumps(movie_list))

    def post(self):
        self.set_header("Content-Type", "application/json")
        user_email = self.get_argument("user_email", default=None)
        user_name = self.get_argument("user_name", default=None)
        screening_id = self.get_argument("screening_id", default=None)
        seat_number = self.get_argument("seat_number", default=None)

        if (
            user_email is None
            or user_name is None
            or screening_id is None
            or seat_number is None
        ):
            self.set_status(400)
            self.write(json.dumps({"error": "Missing field"}))
            return

        try:
            screening_id = UUID(screening_id)
        except ValueError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid screening_id format"}))
            return

        try:
            seat_number = int(seat_number)
        except ValueError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid seat_number format"}))
            return

        res = session.execute(select_movie_by_screening, (screening_id,))
        movie = res.one()
        if movie is None:
            self.set_status(404)
            self.write(json.dumps({"error": "Screening not found"}))
            return

        title = movie.movie_title
        time = movie.screening_time
        total_seats = movie.total_seats
        if seat_number >= total_seats:
            self.set_status(400)
            self.write(json.dumps({"error": "Wrong seat number"}))
            return

        reservation_id = uuid4()

        res = session.execute(
            add_reservation,
            (
                screening_id,
                seat_number,
                reservation_id,
                title,
                time,
                user_name,
                user_email,
            ),
        )
        if res is None:
            self.set_status(500)
            self.write(json.dumps({"error": "Failed to create reservation"}))
            return
        if not res.one().applied:
            self.set_status(409)
            self.write(json.dumps({"error": "Seat already taken"}))
            return

        session.execute(
            add_reservation_user,
            (
                user_email,
                reservation_id,
                user_name,
                screening_id,
                seat_number,
                title,
                time,
            ),
        )

        self.write(json.dumps({"error": None}))
        return

    def put(self):
        self.set_header("Content-Type", "application/json")

        reservation_id = self.get_argument("reservation_id", default=None)
        screening_id = self.get_argument("screening_id", default=None)
        seat_number = self.get_argument("seat_number", default=None)
        user_email = self.get_argument("user_email", default=None)
        new_name = self.get_argument("new_name", default=None)

        if (
            reservation_id is None
            or screening_id is None
            or seat_number is None
            or user_email is None
            or new_name is None
        ):
            self.set_status(400)
            self.write(json.dumps({"error": "Missing field"}))
            return

        try:
            reservation_id = UUID(reservation_id)
            screening_id = UUID(screening_id)
            seat_number = int(seat_number)
        except ValueError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid parameter format"}))
            return

        batch = BatchStatement()
        batch.add(update_reservation, (new_name, screening_id, seat_number))
        batch.add(update_reservation_user, (new_name, user_email, reservation_id))
        res = session.execute(batch)
        if res is None:
            self.set_status(500)
            self.write(json.dumps({"error": "Failed to update reservation"}))
            return

        self.write(json.dumps({"error": None}))


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
        ]
    )


async def main():
    app = make_app()
    app.listen(8888)
    print("Server is running on http://localhost:8888")
    await asyncio.Event().wait()


if __name__ == "__main__":
    session = connect_to_cluster()
    session.set_keyspace("cinema")

    asyncio.run(main())
