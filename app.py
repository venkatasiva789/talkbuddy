import json
import os
from datetime import datetime, date, timezone

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import Config
from models import db, User, ProviderProfile, Booking, Review, Message, Report

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Context processors
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    unread = 0
    if current_user.is_authenticated:
        unread = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return dict(unread_count=unread, now=datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    top_providers = (
        User.query.join(ProviderProfile)
        .filter(User.is_provider.is_(True), ProviderProfile.is_active.is_(True))
        .order_by(ProviderProfile.rating_avg.desc())
        .limit(6)
        .all()
    )
    return render_template("index.html", providers=top_providers)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        city = request.form.get("city", "").strip()

        if not all([name, email, password]):
            flash("All fields are required.", "error")
            return render_template("auth/register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html")

        user = User(name=name, email=email, city=city)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to TalkBuddy!", "success")
        return redirect(url_for("dashboard"))
    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            flash("Welcome back!", "success")
            return redirect(next_page or url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    upcoming_bookings = (
        Booking.query.filter(
            ((Booking.client_id == current_user.id) | (Booking.provider_id == current_user.id)),
            Booking.status.in_(["pending", "confirmed"]),
        )
        .order_by(Booking.date.asc())
        .limit(10)
        .all()
    )
    past_bookings = (
        Booking.query.filter(
            ((Booking.client_id == current_user.id) | (Booking.provider_id == current_user.id)),
            Booking.status.in_(["completed"]),
        )
        .order_by(Booking.date.desc())
        .limit(5)
        .all()
    )
    return render_template("main/dashboard.html", upcoming=upcoming_bookings, past=past_bookings)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.bio = request.form.get("bio", "").strip()
        current_user.city = request.form.get("city", "").strip()
        current_user.languages = request.form.get("languages", "").strip()
        current_user.interests = request.form.get("interests", "").strip()
        current_user.phone = request.form.get("phone", "").strip()
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("edit_profile"))
    return render_template("main/edit_profile.html")


# ---------------------------------------------------------------------------
# Provider setup
# ---------------------------------------------------------------------------
@app.route("/become-provider", methods=["GET", "POST"])
@login_required
def become_provider():
    if current_user.is_provider and current_user.provider_profile:
        return redirect(url_for("provider_dashboard"))
    if request.method == "POST":
        hourly_rate = float(request.form.get("hourly_rate", 25))
        specialties = request.form.get("specialties", "").strip()
        availability = request.form.get("availability", "").strip()
        experience = request.form.get("experience_summary", "").strip()

        current_user.is_provider = True
        if not current_user.bio:
            current_user.bio = request.form.get("bio", "").strip()
        profile = ProviderProfile(
            user_id=current_user.id,
            hourly_rate=hourly_rate,
            specialties=specialties,
            availability=availability,
            experience_summary=experience,
        )
        db.session.add(profile)
        db.session.commit()
        flash("You are now a TalkBuddy provider!", "success")
        return redirect(url_for("provider_dashboard"))
    return render_template("provider/setup.html")


@app.route("/provider/dashboard")
@login_required
def provider_dashboard():
    if not current_user.is_provider:
        return redirect(url_for("become_provider"))
    pending = Booking.query.filter_by(provider_id=current_user.id, status="pending").order_by(Booking.date.asc()).all()
    confirmed = Booking.query.filter_by(provider_id=current_user.id, status="confirmed").order_by(Booking.date.asc()).all()
    completed = (
        Booking.query.filter_by(provider_id=current_user.id, status="completed")
        .order_by(Booking.date.desc())
        .limit(10)
        .all()
    )
    reviews = (
        Review.query.filter_by(reviewee_id=current_user.id).order_by(Review.created_at.desc()).limit(10).all()
    )
    return render_template(
        "provider/dashboard.html", pending=pending, confirmed=confirmed, completed=completed, reviews=reviews
    )


@app.route("/provider/edit", methods=["GET", "POST"])
@login_required
def edit_provider():
    if not current_user.is_provider or not current_user.provider_profile:
        return redirect(url_for("become_provider"))
    profile = current_user.provider_profile
    if request.method == "POST":
        profile.hourly_rate = float(request.form.get("hourly_rate", profile.hourly_rate))
        profile.specialties = request.form.get("specialties", "").strip()
        profile.availability = request.form.get("availability", "").strip()
        profile.experience_summary = request.form.get("experience_summary", "").strip()
        profile.is_active = "is_active" in request.form
        db.session.commit()
        flash("Provider profile updated!", "success")
        return redirect(url_for("provider_dashboard"))
    return render_template("provider/edit.html", profile=profile)


# ---------------------------------------------------------------------------
# Search / Browse
# ---------------------------------------------------------------------------
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    city = request.args.get("city", "").strip()
    language = request.args.get("language", "").strip()
    specialty = request.args.get("specialty", "").strip()
    min_rate = request.args.get("min_rate", type=float)
    max_rate = request.args.get("max_rate", type=float)
    sort = request.args.get("sort", "rating")

    q = User.query.join(ProviderProfile).filter(
        User.is_provider.is_(True), ProviderProfile.is_active.is_(True)
    )

    if query:
        q = q.filter(
            (User.name.ilike(f"%{query}%"))
            | (User.bio.ilike(f"%{query}%"))
            | (ProviderProfile.specialties.ilike(f"%{query}%"))
        )
    if city:
        q = q.filter(User.city.ilike(f"%{city}%"))
    if language:
        q = q.filter(User.languages.ilike(f"%{language}%"))
    if specialty:
        q = q.filter(ProviderProfile.specialties.ilike(f"%{specialty}%"))
    if min_rate is not None:
        q = q.filter(ProviderProfile.hourly_rate >= min_rate)
    if max_rate is not None:
        q = q.filter(ProviderProfile.hourly_rate <= max_rate)

    if sort == "price_low":
        q = q.order_by(ProviderProfile.hourly_rate.asc())
    elif sort == "price_high":
        q = q.order_by(ProviderProfile.hourly_rate.desc())
    elif sort == "bookings":
        q = q.order_by(ProviderProfile.total_bookings.desc())
    else:
        q = q.order_by(ProviderProfile.rating_avg.desc())

    providers = q.limit(50).all()

    providers_map_data = json.dumps([
        {
            "id": p.id,
            "name": p.name,
            "city": p.city,
            "lat": p.latitude,
            "lng": p.longitude,
            "bio": (p.bio[:100] + "...") if len(p.bio) > 100 else p.bio,
            "rating": round(p.provider_profile.rating_avg, 1),
            "rating_count": p.provider_profile.rating_count,
            "rate": round(p.provider_profile.hourly_rate),
            "specialties": p.provider_profile.specialties_list[:3],
            "verified": p.is_verified,
            "initial": p.name[0] if p.name else "?",
        }
        for p in providers
        if p.latitude is not None and p.longitude is not None
    ])

    view = request.args.get("view", "list")
    return render_template("main/search.html", providers=providers, providers_json=providers_map_data, view=view)


# ---------------------------------------------------------------------------
# Provider public profile
# ---------------------------------------------------------------------------
@app.route("/provider/<int:user_id>")
def provider_profile(user_id):
    user = db.session.get(User, user_id)
    if not user or not user.is_provider or not user.provider_profile:
        abort(404)
    reviews = Review.query.filter_by(reviewee_id=user_id).order_by(Review.created_at.desc()).limit(20).all()
    return render_template("provider/profile.html", provider=user, reviews=reviews)


# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------
@app.route("/book/<int:provider_id>", methods=["GET", "POST"])
@login_required
def create_booking(provider_id):
    provider = db.session.get(User, provider_id)
    if not provider or not provider.is_provider:
        abort(404)
    if provider.id == current_user.id:
        flash("You cannot book yourself.", "error")
        return redirect(url_for("provider_profile", user_id=provider_id))

    if request.method == "POST":
        booking_date = request.form.get("date")
        start_time = request.form.get("start_time")
        duration = float(request.form.get("duration", 1))
        meeting_type = request.form.get("meeting_type", "coffee")
        location = request.form.get("location", "").strip()
        notes = request.form.get("notes", "").strip()

        if not booking_date or not start_time:
            flash("Please select a date and time.", "error")
            return redirect(url_for("create_booking", provider_id=provider_id))

        total = provider.provider_profile.hourly_rate * duration
        booking = Booking(
            client_id=current_user.id,
            provider_id=provider_id,
            date=date.fromisoformat(booking_date),
            start_time=start_time,
            duration_hours=duration,
            total_price=total,
            meeting_type=meeting_type,
            meeting_location=location,
            notes=notes,
        )
        db.session.add(booking)
        db.session.commit()
        flash("Booking request sent! Waiting for confirmation.", "success")
        return redirect(url_for("booking_detail", booking_id=booking.id))

    return render_template("booking/create.html", provider=provider)


@app.route("/booking/<int:booking_id>")
@login_required
def booking_detail(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
    if booking.client_id != current_user.id and booking.provider_id != current_user.id:
        abort(403)
    return render_template("booking/detail.html", booking=booking)


@app.route("/booking/<int:booking_id>/confirm", methods=["POST"])
@login_required
def confirm_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.provider_id != current_user.id:
        abort(403)
    booking.status = "confirmed"
    db.session.commit()
    flash("Booking confirmed!", "success")
    return redirect(url_for("booking_detail", booking_id=booking_id))


@app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
    if booking.client_id != current_user.id and booking.provider_id != current_user.id:
        abort(403)
    booking.status = "cancelled"
    db.session.commit()
    flash("Booking cancelled.", "info")
    return redirect(url_for("dashboard"))


@app.route("/booking/<int:booking_id>/complete", methods=["POST"])
@login_required
def complete_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
    if booking.provider_id != current_user.id and booking.client_id != current_user.id:
        abort(403)
    booking.status = "completed"
    if booking.provider.provider_profile:
        booking.provider.provider_profile.total_bookings += 1
    db.session.commit()
    flash("Booking marked as completed!", "success")
    return redirect(url_for("booking_detail", booking_id=booking_id))


@app.route("/bookings")
@login_required
def my_bookings():
    role = request.args.get("role", "client")
    if role == "provider" and current_user.is_provider:
        bookings = Booking.query.filter_by(provider_id=current_user.id).order_by(Booking.date.desc()).all()
    else:
        bookings = Booking.query.filter_by(client_id=current_user.id).order_by(Booking.date.desc()).all()
    return render_template("booking/list.html", bookings=bookings, role=role)


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------
@app.route("/booking/<int:booking_id>/review", methods=["GET", "POST"])
@login_required
def write_review(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.status != "completed":
        abort(404)
    if booking.client_id != current_user.id:
        abort(403)
    if booking.review:
        flash("You already reviewed this booking.", "info")
        return redirect(url_for("booking_detail", booking_id=booking_id))

    if request.method == "POST":
        rating = int(request.form.get("rating", 5))
        comment = request.form.get("comment", "").strip()
        rating = max(1, min(5, rating))

        review = Review(
            booking_id=booking.id,
            reviewer_id=current_user.id,
            reviewee_id=booking.provider_id,
            rating=rating,
            comment=comment,
        )
        db.session.add(review)

        profile = booking.provider.provider_profile
        if profile:
            total_rating = profile.rating_avg * profile.rating_count + rating
            profile.rating_count += 1
            profile.rating_avg = round(total_rating / profile.rating_count, 2)

        db.session.commit()
        flash("Review submitted! Thank you.", "success")
        return redirect(url_for("booking_detail", booking_id=booking_id))

    return render_template("booking/review.html", booking=booking)


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------
@app.route("/messages")
@login_required
def messages_inbox():
    conversations = db.session.execute(
        db.text("""
            SELECT DISTINCT
                CASE WHEN sender_id = :uid THEN receiver_id ELSE sender_id END AS other_id
            FROM messages
            WHERE sender_id = :uid OR receiver_id = :uid
            ORDER BY id DESC
        """),
        {"uid": current_user.id},
    ).fetchall()

    conv_users = []
    for row in conversations:
        other = db.session.get(User, row[0])
        if other:
            last_msg = (
                Message.query.filter(
                    ((Message.sender_id == current_user.id) & (Message.receiver_id == other.id))
                    | ((Message.sender_id == other.id) & (Message.receiver_id == current_user.id))
                )
                .order_by(Message.created_at.desc())
                .first()
            )
            unread = Message.query.filter_by(
                sender_id=other.id, receiver_id=current_user.id, is_read=False
            ).count()
            conv_users.append({"user": other, "last_message": last_msg, "unread": unread})

    return render_template("main/messages.html", conversations=conv_users)


@app.route("/messages/<int:user_id>", methods=["GET", "POST"])
@login_required
def conversation(user_id):
    other = db.session.get(User, user_id)
    if not other or other.id == current_user.id:
        abort(404)

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            msg = Message(sender_id=current_user.id, receiver_id=user_id, content=content)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for("conversation", user_id=user_id))

    Message.query.filter_by(sender_id=user_id, receiver_id=current_user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()

    chat = (
        Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id))
            | ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )
    return render_template("main/conversation.html", other=other, messages=chat)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
@app.route("/report/<int:user_id>", methods=["GET", "POST"])
@login_required
def report_user(user_id):
    reported = db.session.get(User, user_id)
    if not reported or reported.id == current_user.id:
        abort(404)
    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        description = request.form.get("description", "").strip()
        if reason:
            report = Report(
                reporter_id=current_user.id,
                reported_id=user_id,
                reason=reason,
                description=description,
            )
            db.session.add(report)
            db.session.commit()
            flash("Report submitted. Our team will review it.", "success")
            return redirect(url_for("provider_profile", user_id=user_id))
    return render_template("main/report.html", reported=reported)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    total_users = User.query.count()
    total_providers = User.query.filter_by(is_provider=True).count()
    total_bookings = Booking.query.count()
    pending_reports = Report.query.filter_by(status="pending").count()
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(20).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(20).all()
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_providers=total_providers,
        total_bookings=total_bookings,
        pending_reports=pending_reports,
        recent_reports=recent_reports,
        recent_users=recent_users,
    )


@app.route("/admin/report/<int:report_id>/resolve", methods=["POST"])
@login_required
def resolve_report(report_id):
    if not current_user.is_admin:
        abort(403)
    report = db.session.get(Report, report_id)
    if report:
        action = request.form.get("action", "dismiss")
        if action == "warn":
            report.status = "reviewed"
        elif action == "ban":
            report.status = "resolved"
            reported_user = db.session.get(User, report.reported_id)
            if reported_user:
                reported_user.is_active_user = False
        else:
            report.status = "dismissed"
        db.session.commit()
        flash("Report processed.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/verify/<int:user_id>", methods=["POST"])
@login_required
def verify_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = db.session.get(User, user_id)
    if user:
        user.is_verified = True
        db.session.commit()
        flash(f"{user.name} has been verified.", "success")
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# API endpoints (for AJAX)
# ---------------------------------------------------------------------------
@app.route("/api/messages/unread")
@login_required
def api_unread():
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({"unread": count})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/img/uploads"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
