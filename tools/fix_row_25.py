import sqlite3
conn=sqlite3.connect('/workspace/data/app.db')
c=conn.cursor()
print('Before:')
for row in c.execute('SELECT id,user_id,prediction,confidence,glucose,bmi,created_at FROM risk_assessments WHERE id IN (24,25)'):
    print(row)
# Update id 25 to Diabetic
c.execute("UPDATE risk_assessments SET prediction = 'Diabetic' WHERE id = 25")
conn.commit()
print('After:')
for row in c.execute('SELECT id,user_id,prediction,confidence,glucose,bmi,created_at FROM risk_assessments WHERE id IN (24,25)'):
    print(row)
conn.close()
