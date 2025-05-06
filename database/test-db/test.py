import psycopg2
from psycopg2 import sql

def test_pgvector_connection():
    try:
        # Using your provided host, username/password = postgres, db = postgres
        connection_uri = (
            "postgresql://postgres:postgres@"
            ""
            "postgres"
        )

        conn = psycopg2.connect(connection_uri)
        cursor = conn.cursor()

        # Check if the 'documents' table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'documents';
        """)
        result = cursor.fetchone()

        if result:
            print("✅ Connected and table 'documents' exists.")
        else:
            print("⚠️ Connected but table 'documents' does NOT exist.")

        cursor.close()
        conn.close()

    except Exception as e:
        print("❌ Connection failed or error occurred:")
        print(e)

if __name__ == "__main__":
    test_pgvector_connection()
