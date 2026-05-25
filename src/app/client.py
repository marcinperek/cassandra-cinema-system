import argparse
import httpx

BASE_URL = "http://localhost:8888"


def list_movies():
    try:
        r = httpx.get(BASE_URL)
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return []
    
    movies = r.json().get("movie_list", [])
    if not movies:
        print("No movies available.")
        return movies
    print(f"\n{'#':<4} {'Title':<25} {'Time':<22} {'Room':<6}")
    print("-" * 80)
    for i, m in enumerate(movies):
        print(f"{i:<4} {m['title']:<25} {m['time']:<22} {m['room']:<6}")
    return movies


def cmd_list_movies(_args):
    list_movies()


def cmd_my_reservations(args):
    r = httpx.get(BASE_URL, params={"user_email": args.my_reservations})
    if r.status_code == 404:
        print("No reservations found for that email.")
        return
    r.raise_for_status()
    reservations = r.json().get("user_reservations", [])
    if not reservations:
        print("No reservations found.")
        return
    print(f"\n{'#':<4} {'Title':<25} {'Time':<22} {'Seat':<6} {'Name':<20}")
    print("-" * 95)
    for i, res in enumerate(reservations):
        print(
            f"{i:<4} {res['title']:<25} {res['time']:<22} {res['seat']:<6} {res['user_name']:<20}"
        )


def cmd_make_reservation(_args):
    movies = list_movies()
    if not movies:
        return

    while True:
        try:
            choice = int(input("\nSelect movie number: "))
            if 0 <= choice < len(movies):
                break
            print(f"Please enter a number between 0 and {len(movies) - 1}.")
        except ValueError:
            print("Invalid input, enter a number.")

    movie = movies[choice]

    user_name = input("Your name: ").strip()
    user_email = input("Your email: ").strip()

    while True:
        try:
            seat_number = int(input("Seat number: "))
            break
        except ValueError:
            print("Invalid input, enter a number.")

    r = httpx.post(
        BASE_URL,
        params={
            "user_email": user_email,
            "user_name": user_name,
            "screening_id": movie["screening_id"],
            "seat_number": seat_number,
        },
    )

    data = r.json()
    if r.status_code == 200:
        print("Reservation created successfully.")
    else:
        print(f"Error: {data.get('error', r.status_code)}")


def cmd_change_name(_args):
    user_email = input("Your email: ").strip()

    r = httpx.get(BASE_URL, params={"user_email": user_email})
    if r.status_code == 404:
        print("No reservations found for that email.")
        return
    r.raise_for_status()

    reservations = r.json().get("user_reservations", [])
    if not reservations:
        print("No reservations found.")
        return

    print(f"\n{'#':<4} {'Title':<25} {'Time':<22} {'Seat':<6} {'Current Name':<20}")
    print("-" * 95)
    for i, res in enumerate(reservations):
        print(
            f"{i:<4} {res['title']:<25} {res['time']:<22} {res['seat']:<6} {res['user_name']:<20}"
        )

    while True:
        try:
            choice = int(input("\nSelect reservation number to update: "))
            if 0 <= choice < len(reservations):
                break
            print(f"Please enter a number between 0 and {len(reservations) - 1}.")
        except ValueError:
            print("Invalid input, enter a number.")

    selected = reservations[choice]
    new_name = input("New name: ").strip()

    r = httpx.put(
        BASE_URL,
        params={
            "reservation_id": selected["reservation_id"],
            "screening_id": selected["screening_id"],
            "seat_number": selected["seat"],
            "user_email": user_email,
            "new_name": new_name,
        },
    )

    data = r.json()
    if r.status_code == 200:
        print("Name updated successfully.")
    else:
        print(f"Error: {data.get('error', r.status_code)}")


def main():
    parser = argparse.ArgumentParser(description="Cinema reservation CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list_movies", action="store_true", help="List all available movie screenings"
    )
    group.add_argument(
        "--my_reservations", metavar="EMAIL", help="List reservations for a given email"
    )
    group.add_argument(
        "--make_reservation",
        action="store_true",
        help="Interactively make a new reservation",
    )
    group.add_argument(
        "--change_name",
        action="store_true",
        help="Interactively change the name on a reservation",
    )

    args = parser.parse_args()

    if args.list_movies:
        cmd_list_movies(args)
    elif args.my_reservations:
        cmd_my_reservations(args)
    elif args.make_reservation:
        cmd_make_reservation(args)
    elif args.change_name:
        cmd_change_name(args)


if __name__ == "__main__":
    main()
