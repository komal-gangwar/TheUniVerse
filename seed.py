import os
from datetime import datetime, timedelta, timezone
from app import app, db
from models import (
    User, Bus, BusStop, Driver, AcademicResource, Event, Alumni, Faculty,
    Education, Timetable, Club, ClubMembership, CommunityPost, Admin
)


def create_sample_data():
    """Populates the database with sample data."""
    print("Creating sample data...")

    # --- Users ---
    user = User(
        name="John Doe",
        email="john.doe@example.com",
        course="B.Tech",
        branch="Computer Science",
        batch="2025",
        year=3
    )
    user.set_password("password123")

    club_leader = User(
        name="Jane Smith",
        email="jane.smith@example.com",
        course="B.Tech",
        branch="Electrical",
        batch="2024",
        year=4
    )
    club_leader.set_password("password123")

    db.session.add_all([user, club_leader])
    db.session.commit()

    # --- Bus & Driver ---
    bus = Bus(bus_number="UP16A 1234", route_description="Main City Route")
    driver = Driver(name="Amit Kumar", email="amit.driver@campus.edu")
    driver.set_password("driverpass")

    bus.driver = driver
    
    # Add more buses and drivers
    bus2 = Bus(bus_number="UP16A 5678", route_description="North Campus Route")
    driver2 = Driver(name="Raj Singh", email="raj.driver@campus.edu")
    driver2.set_password("driverpass")
    bus2.driver = driver2
    
    bus3 = Bus(bus_number="UP16A 9012", route_description="South Campus Route")
    driver3 = Driver(name="Priya Sharma", email="priya.driver@campus.edu")
    driver3.set_password("driverpass")
    bus3.driver = driver3
    
    db.session.add_all([bus, driver, bus2, driver2, bus3, driver3])
    db.session.commit()

    bus_stops = [
        BusStop(stop_name="Campus Gate", bus=bus, stop_order=1, lat=28.7041, lng=77.1025),
        BusStop(stop_name="City Center", bus=bus, stop_order=2, lat=28.6139, lng=77.2090),
        BusStop(stop_name="Railway Station", bus=bus, stop_order=3, lat=28.6439, lng=77.2290),
    ]
    db.session.add_all(bus_stops)
    db.session.commit()

    # --- Academic Resources ---
    resources = [
        AcademicResource(
            course="B.Tech", branch="Computer Science", year=3, subject="Data Structures",
            resource_type="notes", title="Data Structures Notes", file_path="/files/ds.pdf",
            uploader=user
        ),
        AcademicResource(
            course="B.Tech", branch="Computer Science", year=3, subject="Data Structures",
            resource_type="pyq", title="Data Structures PYQs", file_path="/files/ds_pyq.pdf",
            uploader=club_leader
        ),
        AcademicResource(
            course="B.Tech", branch="Electrical", year=2, subject="Digital Electronics",
            resource_type="syllabus", title="Digital Electronics Syllabus", file_path="/files/de_syllabus.pdf",
            uploader=user
        ),
    ]
    db.session.add_all(resources)
    db.session.commit()

    # --- Events ---
    events = [
        Event(
            title="Annual Tech Fest", description="Where innovation meets inspiration",
            event_date=datetime.now(timezone.utc) + timedelta(days=12, hours=10),
            venue="Main Auditorium", is_highlighted=True, event_type="Cultural"
        ),
        Event(
            title="AI/ML Workshop", description="Hands-on sessions on AI and Machine Learning.",
            event_date=datetime.now(timezone.utc) + timedelta(days=2), venue="CSE Lab",
            event_type="Workshop"
        ),
        Event(
            title="Startup Seminar", description="Learn from successful entrepreneurs.",
            event_date=datetime.now(timezone.utc) + timedelta(days=8), venue="Seminar Hall 1",
            event_type="Seminar"
        ),
        Event(
            title="Hackathon 2023", description="24 hours of non-stop coding.",
            event_date=datetime(2023, 9, 15), venue="CSE Building",
            highlight_images="/static/images/hackathon.jpg"
        ),
        Event(
            title="Annual Music Fest", description="An electrifying night with amazing performances.",
            event_date=datetime(2023, 8, 22), venue="Campus Ground",
            highlight_images="/static/images/music_fest.jpg"
        ),
    ]
    db.session.add_all(events)
    db.session.commit()

    # --- Alumni ---
    alumni1 = Alumni(name="Arjun Sharma", batch="2020", current_designation="Software Engineer", company="Google",
               email="arjun.s@alumni.edu")
    alumni1.set_password("alumni123")
    
    alumni2 = Alumni(name="Priya Singh", batch="2018", current_designation="Product Manager", company="Microsoft",
               email="priya.s@alumni.edu")
    alumni2.set_password("alumni123")
    
    db.session.add_all([alumni1, alumni2])
    db.session.commit()

    # --- Faculty ---
    faculty1 = Faculty(
        name="Dr. Ananya Sharma", designation="Professor", department="Computer Science",
        subjects="Data Structures, Algorithms", photo="/static/images/faculty/ananya.jpg",
        bio="Dr. Ananya Sharma is a distinguished professor in the Department of Computer Science at the University of Innovatech. Her research focuses on artificial intelligence, machine learning, and data science. She has published over 50 peer-reviewed articles and has received numerous awards for her contributions to the field. Dr. Ananya is also an advocate for women in STEM and actively mentors students in her lab.",
        joined_date=datetime(2018, 8, 1).date(), office="Techville Hall 302", phone="(555) 123-4567",
        email="ananya.s@example.edu",
    )
    faculty1.set_password("faculty123")
    
    faculty2 = Faculty(
        name="Dr. Rohan Verma", designation="Professor", department="Electrical",
        subjects="Circuit Theory, Signals", photo="/static/images/faculty/rohan.jpg",
        bio="Dr. Verma is an expert in Electrical and Electronics Engineering with a focus on signal processing and telecommunications. He is known for his practical teaching approach and a passion for research that applies theoretical concepts to real-world problems.",
        joined_date=datetime(2015, 6, 15).date(), office="Electrical Dept. 201", phone="(555) 987-6543",
        email="rohan.v@example.edu",
    )
    faculty2.set_password("faculty123")
    
    db.session.add_all([faculty1, faculty2])
    db.session.commit()

    # --- Faculty Education & Timetable (related to the created faculty) ---
    ananya = Faculty.query.filter_by(name="Dr. Ananya Sharma").first()
    if ananya:
        ananya.education = [
            Education(degree="Ph.D. in Computer Science", university="University of Innovatech", year=2015),
            Education(degree="M.S. in Computer Science", university="University of Techville", year=2012),
            Education(degree="B.S. in Computer Science", university="University of Techville", year=2010),
        ]
        ananya.timetable = [
            Timetable(day="Monday", time="10:00 AM - 11:30 AM", course="Introduction to AI", location="Room 201"),
            Timetable(day="Tuesday", time="1:00 PM - 2:30 PM", course="Machine Learning", location="Room 202"),
            Timetable(day="Wednesday", time="10:00 AM - 11:30 AM", course="Introduction to AI", location="Room 201"),
            Timetable(day="Thursday", time="1:00 PM - 2:30 PM", course="Machine Learning", location="Room 202"),
            Timetable(day="Friday", time="2:00 PM - 3:00 PM", course="Office Hours", location="Room 305"),
        ]
        db.session.commit()

    # --- Clubs & Community Posts ---
    club = Club(name="Tech Innovators", description="A club for all things tech.", secretary=club_leader)
    db.session.add(club)
    db.session.commit()

    membership = ClubMembership(user=user, club=club, is_verified=True, verifier=club_leader)
    # Corrected: use the 'author' relationship property
    community_post = CommunityPost(author=user, content="Welcome to the community!", post_type="Announcement")

    db.session.add_all([membership, community_post])
    db.session.commit()

    # --- Admin ---
    admin_user = Admin(username="superadmin", role="Super Admin")
    admin_user.set_password("adminpass")
    db.session.add(admin_user)
    db.session.commit()

    # --- Bus Manager ---
    from models import BusManager
    bus_manager = BusManager(
        name="Rajesh Verma",
        email="rajesh.manager@campus.edu",
        phone="+91-9876543210"
    )
    bus_manager.set_password("managerpass")
    db.session.add(bus_manager)
    db.session.commit()

    # --- More Users ---
    user3 = User(
        name="Rahul Kapoor",
        email="rahul.k@example.com",
        course="B.Tech",
        branch="Mechanical",
        batch="2026",
        year=2
    )
    user3.set_password("password123")
    
    user4 = User(
        name="Anita Desai",
        email="anita.d@example.com",
        course="B.Tech",
        branch="Civil",
        batch="2025",
        year=3
    )
    user4.set_password("password123")
    
    db.session.add_all([user3, user4])
    db.session.commit()

    # --- More Events ---
    more_events = [
        Event(
            title="Code Sprint 2024",
            description="24-hour coding marathon",
            event_date=datetime.now(timezone.utc) + timedelta(days=5),
            venue="Computer Lab",
            event_type="Competition"
        ),
        Event(
            title="Career Fair",
            description="Meet top recruiters from leading companies",
            event_date=datetime.now(timezone.utc) + timedelta(days=20),
            venue="Convention Center",
            event_type="Career"
        ),
        Event(
            title="Sports Day",
            description="Annual inter-departmental sports competition",
            event_date=datetime.now(timezone.utc) + timedelta(days=15),
            venue="Sports Complex",
            event_type="Sports"
        )
    ]
    db.session.add_all(more_events)
    db.session.commit()

    # --- More Alumni ---
    alumni3 = Alumni(
        name="Vikram Malhotra",
        batch="2019",
        current_designation="Data Scientist",
        company="Amazon",
        email="vikram.m@alumni.edu"
    )
    alumni3.set_password("alumni123")
    
    alumni4 = Alumni(
        name="Sneha Reddy",
        batch="2021",
        current_designation="UX Designer",
        company="Adobe",
        email="sneha.r@alumni.edu"
    )
    alumni4.set_password("alumni123")
    
    db.session.add_all([alumni3, alumni4])
    db.session.commit()

    print("Sample data creation complete!")


if __name__ == '__main__':
    with app.app_context():
        # Only drop and recreate tables if you are in a development environment.
        # This will delete all existing data.
        if os.environ.get('FLASK_ENV') == 'development':
            print("Dropping all tables...")
            db.drop_all()
            print("Creating all tables...")
            db.create_all()
            create_sample_data()
        else:
            print("Not in development environment. Skipping data seeding.")