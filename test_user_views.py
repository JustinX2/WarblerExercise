"""User View tests."""


import os
from unittest import TestCase

from models import db, connect_db, User, Message, Likes
from app import app, CURR_USER_KEY


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
app.config['SQLALCHEMY_ECHO'] = False


app.config['TESTING'] = True
db.create_all()

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 1234
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 5678
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 9012
        self.u2.id = self.u2_id

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")
            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))

    def test_users_query(self):
        with self.client as c:
            resp = c.get("/users?q=testuser")

            self.assertIn("@testuser", str(resp.data))
            self.assertNotIn("@abc", str(resp.data))
            self.assertNotIn("@efg", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("Messages", str(resp.data))
            self.assertIn("Followers", str(resp.data))
            self.assertIn("Following", str(resp.data))

    def test_show_following(self):
        self.testuser.following.append(self.u1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertIn("@abc", str(resp.data))
            self.assertNotIn("@efg", str(resp.data))

    def test_user_follow(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/users/follow/{self.u1_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("unfollow", str(resp.data).lower())

    def test_user_stop_following(self):
        self.testuser.following.append(self.u1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/users/stop-following/{self.u1_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("follow", str(resp.data).lower())

    def test_add_like(self):
        m = Message(id=1984, text="trending warble", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_unlike_message(self):
        m = Message(id=1985, text="trending warble", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()
        like = Likes(user_id=self.testuser_id, message_id=m.id)
        db.session.add(like)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/messages/{m.id}/unlike", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

