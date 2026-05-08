import sqlite3
db_path = r"D:\Capstone Project.new\Capstone Project\backend\data\app.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
print('Before:')
for row in c.execute('SELECT id,user_id,prediction,confidence,glucose,bmi,created_at FROM risk_assessments WHERE id IN (24,25)'):
    print(row)
c.execute("UPDATE risk_assessments SET prediction = 'Diabetic' WHERE id = 25")
conn.commit()
print('After:')
for row in c.execute('SELECT id,user_id,prediction,confidence,glucose,bmi,created_at FROM risk_assessments WHERE id IN (24,25)'):
    print(row)
conn.close()
