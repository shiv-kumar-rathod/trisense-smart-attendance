from getpass import getpass

from app.auth.service import AuthenticationService


def main():
    print("=== Create Reviewer Account ===")

    username = input("Enter reviewer username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    password = getpass("Enter password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")

    if password != confirmation:
        print("Passwords do not match. No account created.")
        return

    try:
        user_id = AuthenticationService().create_user(
            username=username,
            password=password,
            role="reviewer",
        )
        print(f"Reviewer account created successfully. User ID: {user_id}")

    except ValueError as exc:
        print(f"Account creation failed: {exc}")


if __name__ == "__main__":
    main()
