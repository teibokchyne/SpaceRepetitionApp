import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:", [t[0] for t in tables])

# Check spaced_repetition table structure
try:
    cursor.execute("PRAGMA table_info(spaced_repetition)")
    columns = cursor.fetchall()
    print("\nSpaced_repetition columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    # Count rows
    cursor.execute("SELECT COUNT(*) FROM spaced_repetition")
    count = cursor.fetchone()[0]
    print(f"\nPractice items: {count}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
