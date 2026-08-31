import sqlite3
conn = sqlite3.connect('healthcare.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', tables)
for table in tables:
    cursor.execute(f'PRAGMA table_info({table[0]})')
    cols = cursor.fetchall()
    print(f'{table[0]} columns:', cols)
conn.close()