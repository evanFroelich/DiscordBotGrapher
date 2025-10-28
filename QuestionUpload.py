import csv
import sqlite3
import json

CSV_FILE = "Questions/trivia questions.csv"
DB_FILE = "games.db"

def upload_csv_to_db():
    conn = sqlite3.connect(DB_FILE)
    curs = conn.cursor()

    with open(CSV_FILE, newline="", encoding="cp1252") as f:
        reader = csv.DictReader(f, fieldnames=["Subject", "Grade", "Question", "Answer", "Alt1", "Alt2", "Alt3", "Alt4", "Alt5"])
        counter = 0
        for row in reader:
            counter += 1
            if counter % 10 == 0:
                print(f"Processed {counter} rows...")
            # Pass over the row if the first or second column is blank
            if not row["Subject"] or not row["Grade"]:
                continue
            # Build answers list (skip blanks, uppercase for consistency)
            answers = [row["Answer"], row["Alt1"], row["Alt2"], row["Alt3"], row["Alt4"], row["Alt5"]]
            answers = [a.strip().upper() for a in answers if a and a.strip()]

            # Convert to JSON string
            answers_json = json.dumps(answers)

            # Insert into QuestionList
            curs.execute(
                """INSERT INTO QuestionList (Type, Difficulty, Question, Answers)
                   VALUES (?, ?, ?, ?)""",
                (row["Subject"], int(row["Grade"]), row["Question"], answers_json)
            )

    conn.commit()
    conn.close()
    print("✅ Upload complete!")

if __name__ == "__main__":
    upload_csv_to_db()
