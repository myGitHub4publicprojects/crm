import psycopg2
from sonovoxcrm.settings import postres_pass

param = "dbname=crm_db2_copy user=postgres password=%s" % postres_pass

def test():
    conn = psycopg2.connect(param)
    cur = conn.cursor()

    cur.execute("SELECT first_name FROM crm_patient")

    print("The number rows: ", cur.rowcount)

    cur.close()
    conn.close()

def get_patients():
    conn = psycopg2.connect(param)
    cur = conn.cursor()

    cur.execute("SELECT * FROM crm_patient")
    rows = cur.fetchall()
    for i in rows:
        print(i)

    for i in rows[0]:
        print(i)
        print(type(i))

    cur.close()
    conn.close()
