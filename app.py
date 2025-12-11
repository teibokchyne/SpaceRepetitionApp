from flask import Flask, request, redirect
from database import init_db, get_db_connection
from datetime import datetime

app = Flask(__name__)

# Initialize database on app startup
with app.app_context():
    init_db()


def format_date(date_string):
    """Format date string to human-readable format."""
    try:
        if isinstance(date_string, str):
            # Parse ISO format datetime
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            dt = date_string
        # Format as: Monday, December 10, 2025 at 2:30 PM
        return dt.strftime('%A, %B %d, %Y at %I:%M %p')
    except:
        return date_string


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        text = request.form.get('text')
        if text:
            conn = get_db_connection()
            conn.execute('INSERT INTO notes (text) VALUES (?)', (text,))
            conn.commit()
            conn.close()
        return redirect('/')

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    notes_per_page = 20
    offset = (page - 1) * notes_per_page

    # Date filter settings
    filter_type = request.args.get('filter', 'all', type=str)
    filter_date = request.args.get('date', '', type=str)
    sort_order = request.args.get('sort', 'asc', type=str)

    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()

    # Build query based on filter
    query = 'SELECT * FROM notes'
    query_count = 'SELECT COUNT(*) as count FROM notes'

    if filter_type == 'before' and filter_date:
        query += f' WHERE date < "{filter_date}"'
        query_count += f' WHERE date < "{filter_date}"'
    elif filter_type == 'after' and filter_date:
        query += f' WHERE date > "{filter_date}"'
        query_count += f' WHERE date > "{filter_date}"'
    elif filter_type == 'on' and filter_date:
        query += f' WHERE date LIKE "{filter_date}%"'
        query_count += f' WHERE date LIKE "{filter_date}%"'

    # Get total count of notes with filter
    total_notes = conn.execute(query_count).fetchone()['count']

    # Get paginated notes with sort order
    # Sort by date first, then by stars (descending) within the same day
    order_direction = 'DESC' if sort_order == 'desc' else 'ASC'
    query += f' ORDER BY DATE(date) {order_direction}, stars DESC LIMIT ? OFFSET ?'
    notes = conn.execute(query, (notes_per_page, offset)).fetchall()
    conn.close()

    # Calculate total pages
    total_pages = (total_notes + notes_per_page - 1) // notes_per_page

    items_html = ''
    if items:
        items_html = '<ul>'
        for item in items:
            items_html += f'<li>{item["name"]}: {item["description"]}</li>'
        items_html += '</ul>'
    else:
        items_html = '<p>No items in the database yet.</p>'

    notes_html = ''
    if notes:
        notes_html = '<table border="1" style="width:100%; border-collapse: collapse;">'
        notes_html += '<tr><th style="padding: 10px;">Text</th><th style="padding: 10px;">Date</th><th style="padding: 10px;">Importance</th><th style="padding: 10px;">Actions</th><th style="padding: 10px;">Change Date</th></tr>'
        for note in notes:
            formatted_date = format_date(note["date"])
            try:
                stars = note["stars"] if note["stars"] else 0
            except (IndexError, KeyError):
                stars = 0
            star_html = '⭐' * stars if stars > 0 else '✩ (0 stars)'

            # Star rating buttons
            star_buttons = '<div style="display: flex; gap: 3px; flex-wrap: wrap;">'
            for star_count in range(1, 6):
                star_buttons += f'<a href="/rate-note/{note["id"]}/{star_count}" style="padding: 3px 8px; background-color: #FFD700; color: black; text-decoration: none; border-radius: 3px; font-size: 12px; cursor: pointer;">{"⭐" * star_count}</a>'
            star_buttons += '</div>'

            date_buttons = '<div style="display: flex; gap: 5px; flex-wrap: wrap;">'
            for days in [1, 3, 7, 14, 30]:
                date_buttons += f'<a href="/increment-date/{note["id"]}/{days}" style="padding: 3px 8px; background-color: #FF9800; color: white; text-decoration: none; border-radius: 3px; font-size: 12px;">+{days}d</a>'
            date_buttons += '</div>'
            notes_html += f'<tr><td style="padding: 10px;">{note["text"]}</td><td style="padding: 10px;">{formatted_date}</td><td style="padding: 10px;">{star_html}</td><td style="padding: 10px;"><a href="/delete/{note["id"]}" style="margin-right: 10px; padding: 5px 10px; background-color: #f44336; color: white; text-decoration: none; border-radius: 4px;">Delete</a><a href="/edit/{note["id"]}" style="padding: 5px 10px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 4px;">Edit</a></td><td style="padding: 10px;">{date_buttons}</td></tr>'
            notes_html += f'<tr><td colspan="5" style="padding: 5px 10px; background-color: #fafafa;"><strong>Rate:</strong> {star_buttons}</td></tr>'
        notes_html += '</table>'

        # Add pagination controls
        notes_html += '<div style="margin-top: 20px; text-align: center;">'
        notes_html += f'<p>Page {page} of {total_pages} (Total: {total_notes} notes)</p>'
        notes_html += '<div>'

        if page > 1:
            notes_html += f'<a href="/?page=1" style="margin: 0 5px;">First</a>'
            notes_html += f'<a href="/?page={page-1}" style="margin: 0 5px;">Previous</a>'

        notes_html += f'<span style="margin: 0 10px;">Page {page}</span>'

        if page < total_pages:
            notes_html += f'<a href="/?page={page+1}" style="margin: 0 5px;">Next</a>'
            notes_html += f'<a href="/?page={total_pages}" style="margin: 0 5px;">Last</a>'

        notes_html += '</div></div>'
    else:
        notes_html = '<p>No notes yet.</p>'

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Home</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            textarea {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                font-size: 14px;
            }}
            button {{
                padding: 10px 20px;
                font-size: 16px;
                cursor: pointer;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }}
            button:hover {{
                background-color: #45a049;
            }}
            h2 {{
                color: #333;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            table th, table td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            table th {{
                background-color: #4CAF50;
                color: white;
            }}
            table tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h1>Welcome to the Home Page</h1>
        <p>This is a simple Flask application with SQLite database.</p>
        
        <h2>Add a Note</h2>
        <form method="post">
            <textarea name="text" placeholder="Enter your note here..." required></textarea>
            <button type="submit">Save Note</button>
        </form>
        
        <h2>Filter Notes by Date</h2>
        <form method="get" style="margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 4px;">
            <label for="filter" style="margin-right: 10px; font-weight: bold;">Filter Type:</label>
            <select name="filter" id="filter" style="padding: 8px; margin-right: 20px;">
                <option value="all" {"selected" if filter_type == "all" else ""}>All Notes</option>
                <option value="before" {"selected" if filter_type == "before" else ""}>Before Date</option>
                <option value="after" {"selected" if filter_type == "after" else ""}>After Date</option>
                <option value="on" {"selected" if filter_type == "on" else ""}>On Date</option>
            </select>
            <label for="date" style="margin-right: 10px; font-weight: bold;">Date:</label>
            <input type="date" name="date" id="date" value="{filter_date}" style="padding: 8px; margin-right: 20px;">
            <label for="sort" style="margin-right: 10px; font-weight: bold;">Sort Order:</label>
            <select name="sort" id="sort" style="padding: 8px; margin-right: 20px;">
                <option value="asc" {"selected" if sort_order == "asc" else ""}>Oldest First (Ascending)</option>
                <option value="desc" {"selected" if sort_order == "desc" else ""}>Newest First (Descending)</option>
            </select>
            <button type="submit" style="padding: 8px 16px; background-color: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">Filter</button>
            <a href="/" style="padding: 8px 16px; background-color: #999; color: white; text-decoration: none; border-radius: 4px; display: inline-block; margin-left: 10px;">Clear Filter</a>
        </form>
        
        <h2>Notes:</h2>
        {notes_html}
    </body>
    </html>
    '''


@app.route('/delete/<int:note_id>', methods=['GET'])
def delete_note(note_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if request.method == 'POST':
        text = request.form.get('text')
        if text:
            conn = get_db_connection()
            conn.execute('UPDATE notes SET text = ? WHERE id = ?',
                         (text, note_id))
            conn.commit()
            conn.close()
        return redirect('/')

    conn = get_db_connection()
    note = conn.execute('SELECT * FROM notes WHERE id = ?',
                        (note_id,)).fetchone()
    conn.close()

    if note is None:
        return redirect('/')

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Note</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            textarea {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                font-size: 14px;
            }}
            button {{
                padding: 10px 20px;
                font-size: 16px;
                cursor: pointer;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                margin-right: 10px;
            }}
            button:hover {{
                background-color: #45a049;
            }}
            a {{
                padding: 10px 20px;
                font-size: 16px;
                background-color: #999;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
            a:hover {{
                background-color: #777;
            }}
            h1 {{
                color: #333;
            }}
        </style>
    </head>
    <body>
        <h1>Edit Note</h1>
        <form method="post">
            <textarea name="text" required>{note["text"]}</textarea>
            <button type="submit">Update Note</button>
            <a href="/">Cancel</a>
        </form>
    </body>
    </html>
    '''


@app.route('/increment-date/<int:note_id>/<int:days>', methods=['GET'])
def increment_date(note_id, days):
    from datetime import datetime, timedelta

    conn = get_db_connection()
    note = conn.execute('SELECT * FROM notes WHERE id = ?',
                        (note_id,)).fetchone()

    if note:
        current_date = datetime.fromisoformat(
            note['date'].replace('Z', '+00:00'))
        new_date = current_date + timedelta(days=days)
        conn.execute('UPDATE notes SET date = ? WHERE id = ?',
                     (new_date.isoformat(), note_id))
        conn.commit()

    conn.close()
    return redirect('/')


@app.route('/rate-note/<int:note_id>/<int:stars>', methods=['GET'])
def rate_note(note_id, stars):
    """Rate a note with 1-5 stars."""
    if 1 <= stars <= 5:
        conn = get_db_connection()
        conn.execute('UPDATE notes SET stars = ? WHERE id = ?',
                     (stars, note_id))
        conn.commit()
        conn.close()

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
