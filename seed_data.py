"""Populate the database with demo providers and an admin user."""

from app import app, db
from models import User, ProviderProfile, Review, Booking
from datetime import date, datetime, timezone

CITY_COORDS = {
    "Amsterdam": (52.3676, 4.9041),
    "Rotterdam": (51.9225, 4.4792),
    "Utrecht": (52.0907, 5.1214),
    "The Hague": (52.0705, 4.3007),
    "Eindhoven": (51.4416, 5.4697),
}

PROVIDERS = [
    {
        "name": "Emma van Dijk",
        "email": "emma@demo.com",
        "city": "Amsterdam",
        "bio": "Warm and empathetic listener who loves deep conversations about life, culture, and personal growth. I enjoy walking through parks and exploring cozy cafes.",
        "languages": "English, Dutch, German",
        "interests": "Psychology, Art, Philosophy, Cooking",
        "hourly_rate": 30.0,
        "specialties": "Deep Conversations, Life Coaching, Walking Buddy, Coffee Chat",
        "availability": "Mon-Fri 10:00-18:00, Sat 12:00-17:00",
        "experience": "3 years of volunteer counseling experience. Certified life coach. I believe everyone deserves to be heard.",
        "rating": 4.9,
        "rating_count": 47,
        "bookings": 62,
    },
    {
        "name": "Lucas Bakker",
        "email": "lucas@demo.com",
        "city": "Rotterdam",
        "bio": "Friendly social companion who can talk about anything from sports to startups. Great at making people feel comfortable and at ease.",
        "languages": "English, Dutch",
        "interests": "Sports, Technology, Startups, Travel",
        "hourly_rate": 25.0,
        "specialties": "Networking, Career Chat, Walking Buddy, Social Events",
        "availability": "Mon-Sat 09:00-20:00",
        "experience": "Former event organizer turned social companion. I help people build confidence in social situations.",
        "rating": 4.7,
        "rating_count": 35,
        "bookings": 48,
    },
    {
        "name": "Sofia Martinez",
        "email": "sofia@demo.com",
        "city": "Amsterdam",
        "bio": "Bilingual companion from Spain, living in Amsterdam. I love helping newcomers feel at home. Let's grab coffee and talk about anything!",
        "languages": "English, Spanish, Dutch",
        "interests": "Languages, Music, Food, Dancing",
        "hourly_rate": 28.0,
        "specialties": "Language Practice, Cultural Exchange, Coffee Chat, Emotional Support",
        "availability": "Tue-Sun 11:00-19:00",
        "experience": "Community volunteer for 5 years helping expats adjust to life in the Netherlands.",
        "rating": 4.8,
        "rating_count": 52,
        "bookings": 71,
    },
    {
        "name": "Jan de Vries",
        "email": "jan@demo.com",
        "city": "Utrecht",
        "bio": "Retired teacher with a passion for stories. I've lived through decades of change and love sharing wisdom with younger generations.",
        "languages": "English, Dutch, French",
        "interests": "History, Literature, Gardening, Chess",
        "hourly_rate": 20.0,
        "specialties": "Mentoring, Life Stories, Walking Buddy, Companionship",
        "availability": "Daily 10:00-16:00",
        "experience": "30 years as a secondary school teacher. Now I spend my time connecting with people of all ages.",
        "rating": 4.9,
        "rating_count": 28,
        "bookings": 35,
    },
    {
        "name": "Aisha Osman",
        "email": "aisha@demo.com",
        "city": "The Hague",
        "bio": "Social worker turned companion. I specialize in helping people feel less lonely. Let's have a meaningful conversation over coffee or a walk in the park.",
        "languages": "English, Arabic, Dutch",
        "interests": "Wellness, Meditation, Community, Cooking",
        "hourly_rate": 35.0,
        "specialties": "Emotional Support, Mindfulness, Deep Conversations, Coffee Chat",
        "availability": "Mon-Fri 09:00-17:00",
        "experience": "Licensed social worker with 8 years of experience. Trained in active listening and empathetic communication.",
        "rating": 5.0,
        "rating_count": 41,
        "bookings": 55,
    },
    {
        "name": "Thomas Berg",
        "email": "thomas@demo.com",
        "city": "Amsterdam",
        "bio": "Outgoing fitness enthusiast who combines exercise with great conversation. Book me for a walk, run, or gym session with friendly company!",
        "languages": "English, Dutch, Swedish",
        "interests": "Fitness, Nutrition, Outdoor Activities, Music",
        "hourly_rate": 32.0,
        "specialties": "Walking Buddy, Exercise Partner, Motivation, Social Events",
        "availability": "Daily 07:00-20:00",
        "experience": "Personal trainer background. I help people stay active while building genuine connections.",
        "rating": 4.6,
        "rating_count": 23,
        "bookings": 30,
    },
    {
        "name": "Mei Lin Chen",
        "email": "meiling@demo.com",
        "city": "Eindhoven",
        "bio": "Tech professional and creative thinker. I love brainstorming ideas, discussing innovation, and helping people navigate career transitions.",
        "languages": "English, Mandarin, Dutch",
        "interests": "Technology, Design, Innovation, Photography",
        "hourly_rate": 40.0,
        "specialties": "Career Advice, Brainstorming, Networking, Coffee Chat",
        "availability": "Wed-Sun 12:00-20:00",
        "experience": "10 years in the tech industry. Mentor at several startup incubators.",
        "rating": 4.8,
        "rating_count": 19,
        "bookings": 24,
    },
    {
        "name": "Pieter Jansen",
        "email": "pieter@demo.com",
        "city": "Rotterdam",
        "bio": "Easy-going Dutchie who enjoys casual conversations and showing people around the city. Perfect for newcomers wanting to explore Rotterdam!",
        "languages": "English, Dutch",
        "interests": "Architecture, Cycling, Beer, History",
        "hourly_rate": 22.0,
        "specialties": "City Tours, Cultural Exchange, Walking Buddy, Casual Hangout",
        "availability": "Fri-Sun 10:00-18:00",
        "experience": "Born and raised in Rotterdam. I know every hidden gem in the city!",
        "rating": 4.5,
        "rating_count": 31,
        "bookings": 40,
    },
]


def seed():
    with app.app_context():
        db.create_all()

        if User.query.first():
            print("Database already has data. Skipping seed.")
            return

        # Admin user
        lat, lng = CITY_COORDS["Amsterdam"]
        admin = User(
            name="Admin",
            email="admin@talkbuddy.com",
            city="Amsterdam",
            latitude=lat,
            longitude=lng,
            is_admin=True,
            is_verified=True,
        )
        admin.set_password("admin123")
        db.session.add(admin)

        # Demo client
        client = User(
            name="Demo User",
            email="user@demo.com",
            city="Amsterdam",
            latitude=lat,
            longitude=lng,
            bio="Just looking for some friendly conversation and company!",
            languages="English",
            interests="Reading, Travel, Coffee",
            is_verified=True,
        )
        client.set_password("demo123")
        db.session.add(client)

        for p in PROVIDERS:
            clat, clng = CITY_COORDS.get(p["city"], (52.3676, 4.9041))
            user = User(
                name=p["name"],
                email=p["email"],
                city=p["city"],
                latitude=clat,
                longitude=clng,
                bio=p["bio"],
                languages=p["languages"],
                interests=p["interests"],
                is_provider=True,
                is_verified=True,
            )
            user.set_password("demo123")
            db.session.add(user)
            db.session.flush()

            profile = ProviderProfile(
                user_id=user.id,
                hourly_rate=p["hourly_rate"],
                specialties=p["specialties"],
                availability=p["availability"],
                experience_summary=p["experience"],
                rating_avg=p["rating"],
                rating_count=p["rating_count"],
                total_bookings=p["bookings"],
            )
            db.session.add(profile)

        db.session.commit()
        print(f"Seeded {len(PROVIDERS)} providers, 1 client, and 1 admin.")
        print("  Admin login:  admin@talkbuddy.com / admin123")
        print("  Client login: user@demo.com / demo123")
        print("  Provider:     emma@demo.com / demo123  (and others)")


if __name__ == "__main__":
    seed()
