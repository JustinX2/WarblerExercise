"""Message Model Tests."""

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        db.drop_all()
        db.create_all()

        u1 = User.signup("testuser", "test@test.com", "password", None)
        u1.id = 1111
        db.session.commit()

        self.u1 = u1
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):

        m = Message(
            text="a warble",
            user_id=self.u1.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(self.u1.messages[0].text, "a warble")

    def test_message_likes(self):
        m1 = Message(
            text="a warble",
            user_id=self.u1.id
        )

        m2 = Message(
            text="a very interesting warble",
            user_id=self.u1.id
        )

        u2 = User.signup("testuser2", "test2@test.com", "password", None)
        u2.id = 2222
        db.session.add_all([m1, m2, u2])
        db.session.commit()

        u2.likes.append(m1)

        db.session.commit()

        l = Likes.query.filter(Likes.user_id == u2.id).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)

