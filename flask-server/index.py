from flask import Flask, render_template, request, jsonify
import mysql.connector
from datetime import datetime
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

nltk.download('vader_lexicon')

app = Flask(__name__)

# MySQL Connection Details
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'rdx@17'
app.config['MYSQL_DB'] = 'project_neubaitics'


def get_db_connection():
    try:
        mydb = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        return mydb
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/reviews', methods=['POST'])
def submit_review():
    try:
        data = request.get_json()

        user_id = data.get('user_id')
        review_text = data.get('review_text')

        if not user_id or not review_text:
            return jsonify({"error": "Missing required fields"}), 400

        # Sentiment Analysis using NLTK VADER
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(review_text)
        sentiment = "Positive" if scores['compound'] > 0 else "Negative" if scores['compound'] < 0 else "Neutral"
        confidence = abs(scores['compound'])

        db_conn = get_db_connection()
        if db_conn is None:
            return jsonify({"error": "Failed to connect to the database"}), 500

        cursor = db_conn.cursor(buffered=True)
        timestamp = datetime.utcnow()

        query = """
            INSERT INTO reviews (user_id, review_text, sentiment, confidence, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (user_id, review_text, sentiment, confidence, timestamp)

        cursor.execute(query, values)
        db_conn.commit()
        review_id = cursor.lastrowid
        cursor.close()
        db_conn.close()

        return jsonify({
            "message": "Review submitted successfully",
            "review_id": review_id,
            "sentiment": sentiment,
            "confidence": confidence,
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/visualize')
def visualize_data():
    db_conn = get_db_connection()
    if db_conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500
    cursor = db_conn.cursor(dictionary=True)  # use dictionary cursor
    query = "SELECT confidence, timestamp FROM reviews ORDER BY timestamp ASC"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    db_conn.close()

    timestamps = [str(row['timestamp']) for row in results]
    confidenceValues = [float(row['confidence']) for row in results]

    return jsonify({
        "timestamps": timestamps,
        "confidenceValues": confidenceValues
    })


if __name__ == '__main__':
    app.run(debug=True)
