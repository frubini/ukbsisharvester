import mysql.connector


def write_record_to_mysql(rd):
    mydb = mysql.connector.connect(
        host="localhost",
        port="3305",
        user="root",
        password="******",
        database="******"
    )

    my_cursor = mydb.cursor()

    sql = "INSERT INTO narcis (doi, type, datestamp, identifiers, date, title) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (rd['doi'], rd['type'], rd['datestamp'], rd['identifiers'], rd['date'], rd['title'])
    my_cursor.execute(sql, val)

    mydb.commit()
