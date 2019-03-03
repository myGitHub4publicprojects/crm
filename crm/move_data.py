import datetime as dt
import psycopg2
from sonovoxcrm.settings import postres_pass
from crm.ha_list import ha_list

param_source_db = "dbname=crm_db2_copy user=postgres password=%s" % postres_pass
param_target_db = "dbname=crm_db2 user=postgres password=%s" % postres_pass

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
