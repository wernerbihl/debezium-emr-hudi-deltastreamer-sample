import psycopg2
from faker import Faker

fake = Faker()

try:
  # 1. Postgres Connection
  ###################################################

  conn = psycopg2.connect(
    host="containers-us-west-67.railway.app",
    port="5460",
    database="railway",
    user="postgres",
    password="Pi5YIuace0fRq75yPGXq"
  )

  cur = conn.cursor()

  # 2. Create fake data and insert into Postgres
  ###################################################
  def generate_data(amount):

    for _ in range(amount):
      data = (
        fake.name(),
        fake.ascii_company_email(),
        fake.phone_number(),
        fake.random_element(elements=('IT', 'HR', 'Sales', 'Marketing')),
        fake.random_int(min=10000, max=150000),
        fake.date()
      )

      cur.execute('INSERT INTO employees (full_name, email, phone, department, salary, created_at) VALUES (%s,%s,%s,%s,%s,%s)', data)

      print('INSERTED', data)

    conn.commit()

  generate_data(5)

  if conn is not None:
    conn.close()

except (Exception, psycopg2.DatabaseError) as error:
  print(error)

