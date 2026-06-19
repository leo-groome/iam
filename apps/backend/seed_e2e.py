import asyncio
import os
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

# Set default test database url for local use
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_e2e.db")

from app.models.course import Course, Module, Topic
from app.models.user import User
from app.models.base import Base

async def seed():
    database_url = os.environ["DATABASE_URL"]
    print(f"Seeding database at: {database_url}")
    
    # SQLite compatibility for async engine
    kwargs = {}
    if database_url.startswith("sqlite"):
        kwargs["pool_pre_ping"] = True
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
        kwargs["pool_pre_ping"] = True
        
    engine = create_async_engine(database_url, **kwargs)
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with AsyncSessionLocal() as db:
        # 1. Seed mock users
        result = await db.execute(select(User).where(User.neon_user_id == "mock_student_id"))
        student = result.scalar_one_or_none()
        if not student:
            student = User(
                neon_user_id="mock_student_id",
                email="student@example.com",
                full_name="Student User",
                birth_date=date(2000, 1, 1),
                role="estudiante",
                status="activo",
            )
            db.add(student)
            print("Seeded student user.")
            
        result = await db.execute(select(User).where(User.neon_user_id == "mock_admin_id"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                neon_user_id="mock_admin_id",
                email="admin@example.com",
                full_name="Admin User",
                birth_date=date(1990, 1, 1),
                role="admin",
                status="activo",
            )
            db.add(admin)
            print("Seeded admin user.")

        # 2. Seed test course
        result = await db.execute(select(Course).where(Course.slug == "comunicacion-empatica"))
        existing_course = result.scalar_one_or_none()
        if existing_course:
            await db.commit()
            print("Database already seeded with course.")
            return
            
        # Create course
        course = Course(
            slug="comunicacion-empatica",
            title="Comunicación Empática",
            short_desc="Aprende a comunicarte de manera clara y con empatía en el entorno profesional.",
            long_desc="Este curso está diseñado para guiarte a través de los conceptos fundamentales de la comunicación no violenta y empática.",
            age_min=13,
            age_max=99,
            order_index=1,
            status="publicado"
        )
        db.add(course)
        await db.flush() # get course id
        
        # Create module
        module = Module(
            course_id=course.id,
            title="Módulo 1: Fundamentos",
            description="Conceptos iniciales y teoría",
            order_index=1
        )
        db.add(module)
        await db.flush() # get module id
        
        # Create topic
        topic = Topic(
            module_id=module.id,
            title="Video de Introducción",
            content_type="video",
            content_body="Este es el cuerpo del video introductorio.",
            duration_seconds=120,
            has_exam=False,
            order_index=1
        )
        db.add(topic)
        
        await db.commit()
        print("Successfully seeded test_e2e.db with mock users, course, module, and topic!")

if __name__ == "__main__":
    asyncio.run(seed())
