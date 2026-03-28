from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(300), default="")
    bio = db.Column(db.Text, default="")
    city = db.Column(db.String(100), default="")
    languages = db.Column(db.String(300), default="")
    interests = db.Column(db.String(500), default="")
    phone = db.Column(db.String(20), default="")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    is_provider = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    provider_profile = db.relationship("ProviderProfile", backref="user", uselist=False, lazy=True)
    bookings_as_client = db.relationship(
        "Booking", foreign_keys="Booking.client_id", backref="client", lazy=True
    )
    bookings_as_provider = db.relationship(
        "Booking", foreign_keys="Booking.provider_id", backref="provider", lazy=True
    )
    sent_messages = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="sender", lazy=True
    )
    received_messages = db.relationship(
        "Message", foreign_keys="Message.receiver_id", backref="receiver", lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def languages_list(self):
        return [lang.strip() for lang in self.languages.split(",") if lang.strip()] if self.languages else []

    @property
    def interests_list(self):
        return [i.strip() for i in self.interests.split(",") if i.strip()] if self.interests else []


class ProviderProfile(db.Model):
    __tablename__ = "provider_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    hourly_rate = db.Column(db.Float, nullable=False, default=25.0)
    specialties = db.Column(db.String(500), default="")
    availability = db.Column(db.Text, default="")
    experience_summary = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)

    rating_avg = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    total_bookings = db.Column(db.Integer, default=0)

    @property
    def specialties_list(self):
        return [s.strip() for s in self.specialties.split(",") if s.strip()] if self.specialties else []


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # "14:00"
    duration_hours = db.Column(db.Float, nullable=False, default=1.0)
    total_price = db.Column(db.Float, nullable=False)

    meeting_type = db.Column(db.String(50), default="coffee")  # coffee, walk, talk, social
    meeting_location = db.Column(db.String(200), default="")
    notes = db.Column(db.Text, default="")

    status = db.Column(db.String(20), default="pending")  # pending, confirmed, completed, cancelled, disputed

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    review = db.relationship("Review", backref="booking", uselist=False, lazy=True)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, unique=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reviewer = db.relationship("User", foreign_keys=[reviewer_id])
    reviewee = db.relationship("User", foreign_keys=[reviewee_id])


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reported_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending")  # pending, reviewed, resolved, dismissed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reporter = db.relationship("User", foreign_keys=[reporter_id])
    reported = db.relationship("User", foreign_keys=[reported_id])
