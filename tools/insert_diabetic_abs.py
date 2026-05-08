import sqlite3
conn=sqlite3.connect('/workspace/data/app.db')
c=conn.cursor()
# Insert sample diabetic assessment for user_id 10
c.execute('''INSERT INTO risk_assessments (user_id, pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree, age, prediction, confidence) VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (10,1,220,95,30,150,34.8,1.0,45,'Diabetic',0.95))
conn.commit()
print('Inserted id', c.lastrowid)
conn.close()
