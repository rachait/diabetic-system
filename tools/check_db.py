import sqlite3
conn=sqlite3.connect('data/app.db')
conn.row_factory=sqlite3.Row
c=conn.cursor()
print('Users (last 20):')
for row in c.execute('SELECT id, username, email FROM users ORDER BY id DESC LIMIT 20'):
    print(row['id'], row['username'], row['email'])
print('\nCounts:')
for row in c.execute("SELECT COUNT(*) as total_assessments, SUM(CASE WHEN prediction='Diabetic' THEN 1 ELSE 0 END) as diabetic_count FROM risk_assessments"):
    print('total_assessments=', row['total_assessments'], 'diabetic_count=', row['diabetic_count'])
conn.close()
