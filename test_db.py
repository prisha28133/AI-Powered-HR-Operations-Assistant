from database import connect_db

try:
    conn = connect_db()
    print("✅ Database Connected Successfully")
    conn.close()

except Exception as e:
    print("❌ Database Connection Failed")
    print(e)