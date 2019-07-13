import datetime as dt
import psycopg2
from sonovoxcrm.settings import postres_pass
from crm.ha_list import ha_list, other

param_source_db = "dbname=crm_db3 user=postgres password=%s" % postres_pass
param_target_db = "dbname=crm_db4 user=postgres password=%s" % postres_pass

def connect_db(f):
    '''connects to source and target db, executes function f, closes connections'''
    conn1 = psycopg2.connect(param_source_db)
    print('connected to source db')
    cur1 = conn1.cursor()
    print('coursor1 set')
    conn2 = psycopg2.connect(param_target_db)
    print('connected to taget db')
    cur2 = conn2.cursor()
    print('coursor1 set')
    f(conn1, cur1, conn2, cur2)
    cur1.close()
    print('cursor1 closed')
    conn1.close()
    print('connection source closed')
    cur2.close()
    print('cursor2 closed')
    conn2.close()
    print('connection tagret closed')


def patient(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_patient")
    rows = cur.fetchall()
    """ get data from old db from model Patient
    columns in old db crm_patient: 
    id|first_name|last_name|date_of_birth|location|phone_no|invoice_date|create_date
    noachcreatedate|noachID|notes|audiometrist_id"""
    for row in rows:
        id = str(row['id'])
        first_name = row['first_name']
        last_name = row['last_name']
        date_of_birth = row['date_of_birth']
        location = row['location']
        phone_no = row['phone_no']
        create_date = row['create_date']
        notes = row['notes']
        audiometrist_id = str(row['audiometrist_id'])

        """create new Patient in new db with id same as old Patient
        columns in new database:
        id|first_name|last_name|date_of_birth|location|phone_no|create_date|notes
        audiometrist_id|apartment_number|city|house_number|street|zip_code|NIP"""

        # instert to new db
        l = [id, first_name, last_name, date_of_birth, location, phone_no, create_date,
        notes, audiometrist_id]
        values = ', '.join(l)
        print(values)
        fields = "id, first_name, last_name, date_of_birth, location, phone_no, create_date, notes, audiometrist_id"
        sql = "INSERT INTO crm_patient (%s) VALUES (%s);" % (
            fields, values)
        cur2.execute(sql)
        conn2.commit()


def newinfo(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_newinfo")
    rows = cur.fetchall()
    """ get data from old db from model NewInfo
    columns in old db crm_newinfo: 
    id|timestamp|note|audiometrist_id|patient_id"""
    for row in rows:
        id = str(row['id'])
        timestamp = row['timestamp']
        note = row['note']
        audiometrist_id = str(row['audiometrist_id'])
        patient_id = str(row['patient_id'])

        """create new NewInfo in new db with id same as old NewInfo
        columns in new database: id|timestamp|note|audiometrist_id|patient_id"""

        # instert to new db
        l = [id, timestamp, note, audiometrist_id, patient_id]
        values = ', '.join(l)
        print(values)
        fields = "id, timestamp, note, audiometrist_id, patient_id"
        sql = "INSERT INTO crm_newinfo (%s) VALUES (%s);" % (
            fields, values)
        cur2.execute(sql)
        conn2.commit()

def ha_stock(conn1, cur1, conn2, cur2):
    id = 1
    for make, v in ha_list.items():
        for family, i in v.items():
            for model, price_gross in i.items():
                # print('make:', make, 'family:', family, 'model:', model, 'price:', price)
                fields = "id, make, family, model, price_gross, vat_rate, pkwiu_code, added"
                t = (str(id), "'" + make + "'", "'" + family + "'", "'" + model + "'",
                    str(price_gross), '8', "E'26.60.14'", "'" + str(dt.date.today()) + "'")
                values = ', '.join(t)
                print(values)
                sql = "INSERT INTO crm_hearing_aid_stock (%s) VALUES (%s);" % (
                    fields, values)
                cur2.execute(sql)
                conn2.commit()
                id += 1


def pcpr(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_pcpr_estimate")
    rows = cur.fetchall()
    # get data from PCPR_Estimate and Hearing_Aid_Main
    for row in rows:
        date = row['date']
        in_progress = row['in_progress']
        patient_id = row['patient_id']
        ha_main_id = row[0]
        print(row)
        sql = "SELECT * FROM crm_hearing_aid_main WHERE id=%s" % ha_main_id
        cur.execute(sql)
        ha_main = cur.fetchone()
        ha_make = ha_main['ha_make']
        ha_family = ha_main['ha_family']
        ha_model = ha_main['ha_model']
        ear = ha_main['ear']
        current = ha_main['current']
        print('in pr: ', in_progress)

        # create new PCPR_Estimate
        # set PCPR_Estimate id same as old Hearing_Aid_Main
        # columns in database: id | timestamp | updated | current | patient_id

        timestamp = updated = "'" + str(date) + ' 18:12:59.667669' + "'"
        fields = "id, timestamp, updated, current, patient_id"
        l = [str(ha_main_id), timestamp, updated, str(in_progress), str(patient_id)]
        values = ', '.join(l)
        print('values: ', values)
        sql = "INSERT INTO crm_pcpr_estimate (%s) VALUES (%s);" % (
            fields, values)
        cur2.execute(sql)
        conn2.commit()

        # create new Hearing_Aid
        # set id same as old Hearing_Aid_Main
        # columns in database: id | make | family | model | price_gross | vat_rate
        # pkwiu_code | ear | current | purchase_date* | our | estimate_id* | invoice_id* |
        # patient_id | pro_forma_id*
        # those with * are not required

        id = estimate_id = str(ha_main_id)
        make = "'" + ha_make + "'"
        family = "'" + ha_family.upper() + "'"
        model = "'" + ha_model.upper() + "'"
        ear = "'" + ha_main['ear'] + "'"
        current = str(False)
        our = str(False)
        patient_id = str(patient_id)

        # get price from Hearing_Aid_Stock
        conditions = "WHERE make = %s AND family = %s AND  model = %s" % (
            make, family, model)
        sql = "SELECT * FROM crm_hearing_aid_stock " + conditions + ';'
        print(sql)
        cur2.execute(sql)
        ha_stock = cur2.fetchone()
        print('ha stock: ', ha_stock)
        if ha_stock == None:
            price_gross = '0'
        else:
            price_gross = str(ha_stock[4])
        pkwiu_code = "E'26.60.14'"
        vat_rate = '8'

        # instert to new db
        l = [id, make, family, model, price_gross, vat_rate, pkwiu_code, ear, current, our, estimate_id, patient_id]
        values = ', '.join(l)
        print(values)
        fields = "id, make, family, model, price_gross, vat_rate, pkwiu_code, ear, current, our, estimate_id, patient_id"
        sql = "INSERT INTO crm_hearing_aid (%s) VALUES (%s);" % (
            fields, values)

        cur2.execute(sql)
        conn2.commit()


def invoice(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_ha_invoice")
    rows = cur.fetchall()
    # get data from HA_Invoice and Hearing_Aid_Main
    for row in rows:
        date = row['date']
        in_progress = row['in_progress']
        patient_id = row['patient_id']
        ha_main_id = row[0]
        print(row)
        sql = "SELECT * FROM crm_hearing_aid_main WHERE id=%s" % ha_main_id
        cur.execute(sql)
        ha_main = cur.fetchone()
        ha_make = ha_main['ha_make']
        ha_family = ha_main['ha_family']
        ha_model = ha_main['ha_model']
        ear = ha_main['ear']
        current = ha_main['current']
        print('in pr: ', in_progress)

        # create new Invoice
        # set PCPR_Estimate id same as old Hearing_Aid_Main
        # columns in database: id | timestamp | updated | current | patient_id | type | payed

        timestamp = updated = "'" + str(date) + ' 18:12:59.667669' + "'"
        fields = "id, timestamp, updated, current, patient_id, payed, type"
        l = [str(ha_main_id), timestamp, updated,
             str(in_progress), str(patient_id), 'True', "'" + 'cash' + "'"]
        values = ', '.join(l)
        print('values: ', values)
        sql = "INSERT INTO crm_invoice (%s) VALUES (%s);" % (
            fields, values)
        cur2.execute(sql)
        conn2.commit()

        # create new Hearing_Aid
        # set id same as old Hearing_Aid_Main
        # columns in database: id | make | family | model | price_gross | vat_rate
        # pkwiu_code | ear | current | purchase_date* | our | estimate_id* | invoice_id* |
        # patient_id | pro_forma_id*
        # those with * are not required

        id = invoice_id = str(ha_main_id)
        make = "'" + ha_make + "'"
        family = "'" + ha_family.upper() + "'"
        model = "'" + ha_model.upper() + "'"
        ear = "'" + ha_main['ear'] + "'"
        current = str(False)
        our = str(False)
        patient_id = str(patient_id)

        # get price from Hearing_Aid_Stock
        conditions = "WHERE make = %s AND family = %s AND  model = %s" % (
            make, family, model)
        sql = "SELECT * FROM crm_hearing_aid_stock " + conditions + ';'
        print(sql)
        cur2.execute(sql)
        ha_stock = cur2.fetchone()
        print('ha stock: ', ha_stock)
        if ha_stock == None:
            price_gross = '0'
        else:
            price_gross = str(ha_stock[4])
        pkwiu_code = "E'26.60.14'"
        vat_rate = '8'

        # instert to new db
        l = [id, make, family, model, price_gross, vat_rate,
             pkwiu_code, ear, current, our, invoice_id, patient_id]
        values = ', '.join(l)
        print(values)
        fields = "id, make, family, model, price_gross, vat_rate, pkwiu_code, ear, current, our, invoice_id, patient_id"
        sql = "INSERT INTO crm_hearing_aid (%s) VALUES (%s);" % (
            fields, values)

        cur2.execute(sql)
        conn2.commit()


def ha(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_hearing_aid")
    rows = cur.fetchall()
    # get data from Hearing_Aid and Hearing_Aid_Main
    # columns in HA: hearing_aid_main_ptr_id | purchase_date | our | patient_id
    for row in rows:
        our = row['our']
        purchase_date = str(row['purchase_date'])
        if purchase_date != 'None':
            purchase_date = "'" + purchase_date + "'"
        else:
            purchase_date = 'NULL'
        patient_id = row['patient_id']
        ha_main_id = row[0]
        # print(row)
        sql = "SELECT * FROM crm_hearing_aid_main WHERE id=%s" % ha_main_id
        cur.execute(sql)
        ha_main = cur.fetchone()
        ha_make = ha_main['ha_make']
        ha_family = ha_main['ha_family']
        ha_model = ha_main['ha_model']
        ear = ha_main['ear']
        current = ha_main['current']

        # create new Hearing_Aid
        # set id same as old Hearing_Aid_Main
        # columns in database: id | make | family | model | price_gross | vat_rate
        # pkwiu_code | ear | current | purchase_date* | our | estimate_id* | invoice_id* |
        # patient_id | pro_forma_id*
        # those with * are not required

        id = str(ha_main_id)
        make = "'" + ha_make + "'"
        family = "'" + ha_family.upper() + "'"
        model = "'" + ha_model.upper() + "'"
        ear = "'" + ha_main['ear'] + "'"
        current = str(current)
        our = str(our)
        patient_id = str(patient_id)
        price_gross = '0'
        vat_rate = '8'
        pkwiu_code = "E'26.60.14'"

        # instert to new db
        l = [id, make, family, model, price_gross, vat_rate,
             pkwiu_code, ear, current, purchase_date, our, patient_id]
        values = ', '.join(l)
        print(values)
        fields = "id, make, family, model, price_gross, vat_rate, pkwiu_code, ear, current, purchase_date, our, patient_id"
        sql = "INSERT INTO crm_hearing_aid (%s) VALUES (%s);" % (
            fields, values)

        cur2.execute(sql)
        conn2.commit()


def other_stock(conn1, cur1, conn2, cur2):
    id = 1
    for make, v in other.items():
        for family, i in v.items():
            for model, price_gross in i.items():
                # print('make:', make, 'family:', family, 'model:', model, 'price:', price)
                fields = "id, make, family, model, price_gross, vat_rate, pkwiu_code, added"
                t = (str(id), "'" + make + "'", "'" + family + "'", "'" + model + "'",
                     str(price_gross), '8', "E'26.60.14'", "'" + str(dt.date.today()) + "'")
                values = ', '.join(t)
                print(values)
                sql = "INSERT INTO crm_other_item_stock (%s) VALUES (%s);" % (
                    fields, values)
                cur2.execute(sql)
                conn2.commit()
                id += 1


def nfz_new(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_nfz_new")
    rows = cur.fetchall()
    # get data from NFZ_New and NFZ
    # columns in NFZ_New: nfz_ptr_id | patient_id
    for row in rows:
        patient_id = row['patient_id']
        nfz_id = row[0]

        sql = "SELECT * FROM crm_nfz WHERE id=%s" % nfz_id
        cur.execute(sql)
        # columns in nfz: id | date | side | in_progress
        nfz = cur.fetchone()
        id = str(nfz_id)
        date = nfz['date']
        side = nfz['side']
        in_progress = nfz['in_progress']

        # create new NFZ_New
        # set id same as old NFZ
        # columns in database: id | date | side | in_progress | patient_id

        sql = """INSERT INTO crm_nfz_new (id, date, side, in_progress, patient_id)
        VALUES ( %(id)s, %(date)s, %(side)s, %(in_progress)s, %(patient_id)s);"""

        data = {'id': id,
                'date': date,
                'side': side,
                'in_progress': in_progress,
                'patient_id': patient_id
                }
        
        print(sql)
        cur2.execute(sql, data)
        conn2.commit()


def nfz_conf(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_nfz_confirmed")
    rows = cur.fetchall()
    # get data from NFZ_Confirmed and NFZ
    # columns in NFZ_Confirmed: nfz_ptr_id | patient_id
    for row in rows:
        patient_id = row['patient_id']
        nfz_id = row[0]

        sql = "SELECT * FROM crm_nfz WHERE id=%s" % nfz_id
        cur.execute(sql)
        # columns in nfz: id | date | side | in_progress
        nfz = cur.fetchone()
        id = str(nfz_id)
        date = nfz['date']
        side = nfz['side']
        in_progress = nfz['in_progress']

        # create new NFZ_Confirmed
        # set id same as old NFZ
        # columns in database: id | date | side | in_progress | patient_id

        sql = """INSERT INTO crm_nfz_confirmed (id, date, side, in_progress, patient_id)
        VALUES ( %(id)s, %(date)s, %(side)s, %(in_progress)s, %(patient_id)s);"""

        data = {'id': id,
                'date': date,
                'side': side,
                'in_progress': in_progress,
                'patient_id': patient_id
                }

        print(sql)
        cur2.execute(sql, data)
        conn2.commit()


def reminder_new(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_reminder WHERE nfz_new_id is not NULL")
    rows = cur.fetchall()
    # get data from Reminder
    # columns in Reminder: id, active, timestamp, activation_date, ha_id* invoice_id*, nfz_confirmed_id*, pcpr_id*, nfz_new_id*
    for row in rows:
        print(row)
        # create Reminder_New
        # set id same as old Reminder
        # columns in database: id | active | timestamp | activation_date | nfz_new_id
        data = {'id': row['id'],
                'active': row['active'],
                'timestamp': row['timestamp'],
                'activation_date': row['activation_date'],
                'nfz_new_id': row['nfz_new_id'],
                }

        sql = """INSERT INTO crm_reminder_nfz_new (id, active, timestamp, activation_date, nfz_new_id)
        VALUES ( %(id)s, %(active)s, %(timestamp)s, %(activation_date)s, %(nfz_new_id)s);"""

        print(sql)
        cur2.execute(sql, data)
        conn2.commit()


def reminder_conf(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_reminder WHERE nfz_confirmed_id is not NULL")
    rows = cur.fetchall()
    # get data from Reminder
    # columns in Reminder: id, active, timestamp, activation_date, ha_id* invoice_id*, nfz_confirmed_id*, pcpr_id*, nfz_new_id*
    for row in rows:
        print(row)
        # create Reminder_NFZ_Confirmed
        # set id same as old Reminder
        # columns in database: id | active | timestamp | activation_date | nfz_confirmed_id
        data = {'id': row['id'],
                'active': row['active'],
                'timestamp': row['timestamp'],
                'activation_date': row['activation_date'],
                'nfz_confirmed_id': row['nfz_confirmed_id'],
                }

        sql = """INSERT INTO crm_reminder_nfz_confirmed (id, active, timestamp, activation_date, nfz_confirmed_id)
        VALUES ( %(id)s, %(active)s, %(timestamp)s, %(activation_date)s, %(nfz_confirmed_id)s);"""

        print(sql)
        cur2.execute(sql, data)
        conn2.commit()


def reminder_pcpr(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_reminder WHERE pcpr_id is not NULL")
    rows = cur.fetchall()
    # get data from Reminder
    # columns in Reminder: id, active, timestamp, activation_date, ha_id* invoice_id*, nfz_confirmed_id*, pcpr_id*, nfz_new_id*
    for row in rows:
        print(row)
        # create Reminder_PCPR
        # set id same as old Reminder
        # columns in database: id | active | timestamp | activation_date | pcpr_id
        data = {'id': row['id'],
                'active': row['active'],
                'timestamp': row['timestamp'],
                'activation_date': row['activation_date'],
                'pcpr_id': row['pcpr_id'],
                }

        sql = """INSERT INTO crm_reminder_pcpr (id, active, timestamp, activation_date, pcpr_id)
        VALUES ( %(id)s, %(active)s, %(timestamp)s, %(activation_date)s, %(pcpr_id)s);"""

        print(sql)
        cur2.execute(sql, data)
        conn2.commit()


def reminder_invoice(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_reminder WHERE invoice_id is not NULL")
    rows = cur.fetchall()
    # get data from Reminder
    # columns in Reminder: id, active, timestamp, activation_date, ha_id* invoice_id*, nfz_confirmed_id*, pcpr_id*, nfz_new_id*
    for row in rows:
        print(row)
        # create Reminder_Invoice
        # set id same as old Reminder
        # columns in database: id | active | timestamp | activation_date | invoice_id
        data = {'id': row['id'],
                'active': row['active'],
                'timestamp': row['timestamp'],
                'activation_date': row['activation_date'],
                'invoice_id': row['invoice_id'],
                }

        sql = """INSERT INTO crm_reminder_invoice (id, active, timestamp, activation_date, invoice_id)
        VALUES ( %(id)s, %(active)s, %(timestamp)s, %(activation_date)s, %(invoice_id)s);"""

        print(sql)
        cur2.execute(sql, data)
        conn2.commit()


def reminder_collection(conn1, cur1, conn2, cur2):
    cur = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM crm_reminder WHERE ha_id is not NULL")
    rows = cur.fetchall()
    # get data from Reminder
    # columns in Reminder: id, active, timestamp, activation_date, ha_id* invoice_id*, nfz_confirmed_id*, pcpr_id*, nfz_new_id*
    for row in rows:
        print(row)
        # create Reminder_Collection
        # set id same as old Reminder
        # columns in database: id | active | timestamp | activation_date | collection_id
        data = {'id': row['id'],
                'active': row['active'],
                'timestamp': row['timestamp'],
                'activation_date': row['activation_date'],
                'ha_id': row['ha_id'],
                }

        sql = """INSERT INTO crm_reminder_collection (id, active, timestamp, activation_date, ha_id)
        VALUES ( %(id)s, %(active)s, %(timestamp)s, %(activation_date)s, %(ha_id)s);"""

        print(sql)
        cur2.execute(sql, data)
        conn2.commit()

def run_all():
    functions = (patient, newinfo, ha_stock, pcpr, invoice, ha, other_stock, nfz_new, nfz_conf,
                 reminder_new, reminder_conf, reminder_pcpr, reminder_invoice, reminder_collection)
    for f in functions:
        connect_db(f)
