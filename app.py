from flask import Flask, render_template, request, redirect, url_for, session
from utils.db_helper import get_connection
import json
import os  # ✅ Added to handle path for questions.json

app = Flask(__name__)
app.secret_key = 'quiz application'  # Used for session management

# ---------------------------------
# Database Connection Test (Startup)
# ---------------------------------
try:
    conn = get_connection()
    print("✅ Connected to the database!")
    conn.close()
except Exception as e:
    print("❌ Failed to connect to the database:", e)

# -------------------------
# Helper Function
# -------------------------
def get_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM questions")
    categories = cursor.fetchall()
    conn.close()
    return categories

# -------------------------
# Routes
# -------------------------

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return f"Error: {e}"
        finally:
            conn.close()

        session['username'] = username
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/explore')
def explore():
    if 'username' not in session:
        return redirect(url_for('login'))

    categories = get_categories()
    return render_template('explore.html', categories=categories)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        category = request.form['category']
        num_questions = int(request.form['num_questions'])
        difficulty = request.form['difficulty']
        quiz_type = request.form['type']
        time_per_question = int(request.form['time_per_question'])

        json_categories = ['general', 'science', 'tech', 'history', 'sports']
        if category in json_categories:
            try:
                # ✅ Use safe and absolute path
                json_path = os.path.join(os.path.dirname(__file__), 'questions.json')
                with open(json_path, 'r') as f:
                    all_questions = json.load(f)

                selected_category_questions = all_questions.get(category, [])
                filtered = [
                    q for q in selected_category_questions
                    if (q['difficulty'] == difficulty or difficulty == 'any') and (q['type'] == quiz_type or quiz_type == 'any')
                ]
                selected_questions = filtered[:num_questions]

                session['quiz_questions'] = selected_questions  # ✅ Store in session for result calculation
                return render_template('play_quiz.html', questions=selected_questions, timer=time_per_question)
            except FileNotFoundError:
                return "❌ Error: questions.json not found. Please make sure it's in the same folder as app.py."

        # Load from database
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if category and category != "any":
            query += " AND category = %s"
            params.append(category)
        if difficulty and difficulty != "any":
            query += " AND difficulty = %s"
            params.append(difficulty)
        if quiz_type and quiz_type != "any":
            query += " AND qtype = %s"
            params.append(quiz_type)

        query += " ORDER BY RAND() LIMIT %s"
        params.append(num_questions)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        quiz_questions = []
        for row in rows:
            question = {
                'question': row[1],
                'options': [row[2], row[3], row[4], row[5]],
                'correct_answer': row[6],
                'type': row[9]
            }
            quiz_questions.append(question)

        session['quiz_questions'] = quiz_questions  # ✅ Store in session for result calculation
        return render_template('play_quiz.html', questions=quiz_questions, timer=time_per_question)

    return render_template('quiz.html')

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'quiz_questions' not in session:
        return redirect(url_for('quiz'))

    user_answers = request.form.to_dict()
    correct_answers = {f"q{i+1}": q['correct_answer'] for i, q in enumerate(session['quiz_questions'])}

    print("User Answers:", user_answers)  # Debugging
    print("Correct Answers:", correct_answers)  # Debugging

    score = sum(1 for key in correct_answers if key in user_answers and user_answers[key].strip().lower() == correct_answers[key].strip().lower())
    total_questions = len(correct_answers)

    session['score'] = score
    session['total_questions'] = total_questions
    session.pop('quiz_questions', None)

    return redirect(url_for('result'))


@app.route('/result', methods=['GET', 'POST'])
def result():
    score = session.get('score', 0)
    total_questions = session.get('total_questions', 0)

    return render_template('result.html', score=score, total_questions=total_questions)

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        q = request.form['question']
        a = request.form['option_a']
        b = request.form['option_b']
        c = request.form['option_c']
        d = request.form['option_d']
        correct = request.form['correct_option']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, correct_option) VALUES (%s, %s, %s, %s, %s, %s)",
                       (q, a, b, c, d, correct))
        conn.commit()
        conn.close()
        return "Question added!"
    
    return render_template('add_question.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/check_users')
def check_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)
