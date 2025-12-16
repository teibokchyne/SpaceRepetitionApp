import sqlite3
import json
import os

DATABASE_PATH = 'app.db'


def backup_all_data():
    """Backup all data from the database."""
    if not os.path.exists(DATABASE_PATH):
        print("Database file not found.")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    backup_data = {}

    # Backup items table
    try:
        items = cursor.execute('SELECT * FROM items').fetchall()
        backup_data['items'] = [dict(row) for row in items]
        print(f"Backed up {len(items)} items")
    except Exception as e:
        print(f"Error backing up items: {e}")

    # Backup notes table
    try:
        notes = cursor.execute('SELECT * FROM notes').fetchall()
        backup_data['notes'] = [dict(row) for row in notes]
        print(f"Backed up {len(notes)} notes")
    except Exception as e:
        print(f"Error backing up notes: {e}")

    # Backup practices table
    try:
        practices = cursor.execute(
            'SELECT * FROM spaced_repetition').fetchall()
        backup_data['practices'] = [dict(row) for row in practices]
        print(f"Backed up {len(practices)} practices")
    except Exception as e:
        print(f"Error backing up practices: {e}")

    conn.close()

    # Save backup to JSON
    with open('full_database_backup.json', 'w') as f:
        json.dump(backup_data, f, indent=2)

    print("Backup saved to full_database_backup.json")
    return backup_data


def restore_all_data():
    """Restore all data from backup after database is recreated."""
    if not os.path.exists('full_database_backup.json'):
        print("Backup file not found.")
        return

    with open('full_database_backup.json', 'r') as f:
        backup_data = json.load(f)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Restore items table
    if 'items' in backup_data:
        for item in backup_data['items']:
            try:
                cursor.execute(
                    'INSERT INTO items (id, name, description, created_at) VALUES (?, ?, ?, ?)',
                    (item['id'], item['name'],
                     item['description'], item['created_at'])
                )
            except Exception as e:
                print(f"Error restoring item: {e}")
        print(f"Restored {len(backup_data['items'])} items")

    # Restore notes table
    if 'notes' in backup_data:
        for note in backup_data['notes']:
            try:
                cursor.execute(
                    'INSERT INTO notes (id, text, date, stars) VALUES (?, ?, ?, ?)',
                    (note['id'], note['text'], note['date'], note['stars'])
                )
            except Exception as e:
                print(f"Error restoring note: {e}")
        print(f"Restored {len(backup_data['notes'])} notes")

    # Restore practices table
    if 'practices' in backup_data:
        for practice in backup_data['practices']:
            try:
                cursor.execute(
                    'INSERT INTO spaced_repetition (id, subject, topic, question, answer, date, stars) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (practice['id'], practice['subject'], practice['topic'], practice['question'],
                     practice['answer'], practice['date'], practice.get('stars', 0))
                )
            except Exception as e:
                print(f"Error restoring practice: {e}")
        print(f"Restored {len(backup_data['practices'])} practices")

    conn.commit()
    conn.close()
    print("Database restore complete")


if __name__ == '__main__':
    print("Starting backup...")
    backup_all_data()

    print("\nDeleting old database...")
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print("Old database deleted")

    print("\nRun your Flask app to recreate the database with new tables...")
    print("Then run: python restore_practices.py")
