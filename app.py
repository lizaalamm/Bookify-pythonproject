from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import random
from datetime import datetime
import os 

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session

# Google Books API Configuration
API_KEY = os.getenv("")

BASE_URL = ""

# Sample books data
POPULAR_GENRES = [
    "Fantasy", "Mystery", "Romance",
    "Science Fiction", "Biography", "History"
]

TESTIMONIALS = [
    {
        "text": "Bookify helped me discover my new favorite author!",
        "author": "Sarah J."
    },
    {
        "text": "The recommendations are always spot on.",
        "author": "Michael T."
    },
    {
        "text": "I've doubled my reading since using Bookify.",
        "author": "Priya K."
    }
]

# Initialize reading list in session if it doesn't exist
@app.before_request
def before_request():
    if 'reading_list' not in session:
        session['reading_list'] = []


@app.route('/')
def home():
    return render_template(
        'index.html',
        popular_genres=POPULAR_GENRES,
        testimonials=TESTIMONIALS,
        current_year=datetime.now().year
    )

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('home'))
    
    try:
        params = {
            'q': query,
            'key': API_KEY,
            'maxResults': 10,
            'printType': 'books'
        }
        
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for item in data.get('items', []):
            volume = item.get('volumeInfo', {})
            book_data = {
                'title': volume.get('title', 'No title'),
                'author': ', '.join(volume.get('authors', ['Unknown'])),
                'description': volume.get('description', 'No description'),
                'thumbnail': volume.get('imageLinks', {}).get('thumbnail', '')
            }
            # Check if book is already in reading list
            book_data['is_saved'] = any(
                book['title'] == book_data['title'] and 
                book['author'] == book_data['author']
                for book in session['reading_list']
            )
            books.append(book_data)
        
        return render_template('results.html',
                            books=books,
                            query=query)
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        return render_template('results.html',
                            books=[],
                            query=query,
                            error=str(e))

@app.route('/save_book', methods=['POST'])
def save_book():
    book_data = {
        'title': request.form.get('title'),
        'author': request.form.get('author'),
        'description': request.form.get('description'),
        'thumbnail': request.form.get('thumbnail') or url_for('static', filename='images/no-cover.png')
    }
    
    # Check if book already exists in reading list
    if not any(
        book['title'] == book_data['title'] and 
        book['author'] == book_data['author']
        for book in session['reading_list']
    ):
        session['reading_list'].append(book_data)
        session.modified = True
        return jsonify({'status': 'success', 'message': 'Book saved to reading list'})
    else:
        return jsonify({'status': 'info', 'message': 'Book already in reading list'})

@app.route('/remove_book', methods=['POST'])
def remove_book():
    title = request.form.get('title')
    author = request.form.get('author')
    
    # Remove book from reading list
    session['reading_list'] = [
        book for book in session['reading_list'] 
        if not (book['title'] == title and book['author'] == author)
    ]
    session.modified = True
    
    return jsonify({'status': 'success', 'message': 'Book removed from reading list'})

@app.route('/readinglist')
def reading_list():
    return render_template(
        'readinglist.html',
        books=session['reading_list'],
        current_year=datetime.now().year
    )

# Add this new route with the existing routes
@app.route('/profile')
def profile():
    # Get reading list count
    reading_list_count = len(session.get('reading_list', []))
    
    # Get current year for the reading challenge
    current_year = datetime.now().year
    
    return render_template(
        'profile.html',
        reading_list_count=reading_list_count,
        current_year=current_year
    )


if __name__ == '__main__':
    app.run(debug=True)