from database import Base, engine

def run_migrations():
    """Create all tables defined in models."""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Running database migrations...")
    run_migrations()
    print("Migrations completed successfully!") 