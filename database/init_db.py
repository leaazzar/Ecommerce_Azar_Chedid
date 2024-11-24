import sqlite3

def init_db():
    with open('database/schema.sql', 'r') as f:
        schema = f.read()

    conn = sqlite3.connect('customers.db')
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()
    conn.close()
    print("Database initialized from schema.sql.")

if __name__ == "__main__":
    init_db()
