import sqlite3
conn=sqlite3.connect('/workspace/data/app.db')
conn.row_factory=sqlite3.Row
c=conn.cursor()
r=c.execute("SELECT COUNT(*) as total_assessments, SUM(CASE WHEN prediction='Diabetic' THEN 1 ELSE 0 END) as diabetic_count FROM risk_assessments").fetchone()
print('total_assessments=', r['total_assessments'], 'diabetic_count=', r['diabetic_count'])
conn.close()
