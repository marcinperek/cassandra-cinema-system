# Distributed cinema reservation system using Cassandra

This project implements simple cinema reservation system using Cassandra as a distributed database. It comes with simple CLI that allows to view movies, view user reservations, make a new reservation and change user name displayed on reservation.

## Setup
1. Install dependencies:
    ```bash
    uv sync
    # or
    pip install -r requirements.txt
    ```
    For stress testing, install `autocannon`:
    ```bash
    npm install autocannon
    ```
2. Start Cassandra:
    ```bash
    docker compose up -d
    ```
    Warning: Cassandra cluster allocates a lot of RAM
3. Run setup script to prepare demo database:
    ```bash
    uv run setup
    ```
4. Start the server:
    ```bash
    uv run server
    ```

## CLI
Available commands:
```bash
uv run client --list_movies
uv run client --my_reservations user@example.com
uv run client --make_reservation      # interactive
uv run client --change_name           # interactive
```

# Stress testing
Stress tests can be run with:
```bash
uv run tests
```
Stress Test 1: The client makes the same request very quickly.
Stress Test 2: Three clients make the possible requests randomly.
Stress Test 3: Two clients try to reserve all seats at the same time.

## Database schema
Movies:
- **screening_id**: UUID
- movie_title: text
- screening_time: timestamp
- room_number: int
- total_seats: int

Reservations:
- **screening_id**: UUID
- **seat_number**: int
- reservation_id: UUID
- movie_title: text
- screening_time: timestamp
- user_name: text
- user_email: text

Reservations_by_user:
- **user_email**: text
- **reservation_id**: UUID
- user_name: text
- screening_id: UUID
- seat_number: int
- movie_title: text
- screening_time: timestamp
