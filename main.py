
from app.bootstrap import initialize_application
from app.ui.app import AttendanceApp
from app.ui.login_window import LoginWindow


def main():
    initialize_application()

    app = AttendanceApp(require_login=True)
    app.run()


if __name__ == "__main__":
    main()
