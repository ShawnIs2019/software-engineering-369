import unittest

from cems import create_app, db
from cems.models import STUDENT, User

VALID = {
    "name": "Sam Student",
    "email": "sam@bowie.edu",
    "password": "correct-horse",
    "confirm_password": "correct-horse",
}


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def register(self, **overrides):
        return self.client.post("/register", data={**VALID, **overrides})

    def login(self, email="sam@bowie.edu", password="correct-horse"):
        return self.client.post("/login", data={"email": email, "password": password})

    def get_user(self, email="sam@bowie.edu"):
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            if user is not None:
                db.session.expunge(user)
            return user


class RegistrationTests(AuthTestCase):
    def test_register_creates_student_and_redirects_to_login(self):
        response = self.register()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])
        user = self.get_user()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, STUDENT)

    def test_password_is_hashed_not_stored_in_plain_text(self):
        self.register()
        user = self.get_user()
        self.assertNotEqual(user.password_hash, VALID["password"])
        self.assertNotIn(VALID["password"], user.password_hash)

    def test_duplicate_email_is_rejected(self):
        self.register()
        response = self.register()
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"already exists", response.data)

    def test_duplicate_check_ignores_email_case(self):
        self.register()
        response = self.register(email="SAM@Bowie.edu")
        self.assertEqual(response.status_code, 400)

    def test_short_password_is_rejected(self):
        response = self.register(password="short", confirm_password="short")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"at least 8", response.data)
        self.assertIsNone(self.get_user())

    def test_password_mismatch_is_rejected(self):
        response = self.register(confirm_password="different-pass")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"do not match", response.data)

    def test_invalid_email_is_rejected(self):
        response = self.register(email="not-an-email")
        self.assertEqual(response.status_code, 400)


class LoginTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.register()

    def test_login_success_redirects_to_dashboard(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])
        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get("user_id"))
            self.assertEqual(sess.get("role"), STUDENT)

    def test_login_is_case_insensitive_for_email(self):
        response = self.login(email="SAM@BOWIE.EDU")
        self.assertEqual(response.status_code, 302)

    def test_wrong_password_fails_with_generic_message(self):
        response = self.login(password="wrong-password")
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid email or password", response.data)

    def test_unknown_email_gives_same_message(self):
        response = self.login(email="nobody@bowie.edu")
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid email or password", response.data)


class SessionTests(AuthTestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_dashboard_shows_user_name_after_login(self):
        self.register()
        self.login()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sam Student", response.data)

    def test_logout_ends_session(self):
        self.register()
        self.login()
        self.client.post("/logout")
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
