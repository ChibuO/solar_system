#for can_recv_app.py
#this is the code that only interacts with the database

import sqlite3
import pkg_resources, os

def getTags():
    # Open and read the file.
    filename = pkg_resources.resource_filename(
        __name__,
        os.path.join('resources', 'mppt_tags.txt'))

    with open(filename) as f:
        contents = f.readlines()
        tags = list(map(lambda d:d.replace('\n', ''), contents))
        return tags

og = ["Timestamp"]
g = []
og.extend(getTags())
print(og)
og_w_type = ["Timestamp TEXT"]
g_w_type = []
og_w_type.extend(list(map(lambda tag: tag + " REAL", og[1:])))
og_w_type_string = ', '.join(og_w_type)
print(og_w_type_string)
og_string = ', '.join(og)
print(og_string)
q_marks = ', '.join(['?' for i in og])
print(q_marks)

tableName = "new_table"

#add queries separately so it's easier to change later on
CREATE_CAN_TABLE = f"""CREATE TABLE IF NOT EXISTS {tableName} 
({og_w_type_string});"""
#id INTEGER PRIMARY KEY, 
INSERT_ROW = f"INSERT INTO {tableName} ({og_string}) VALUES ({q_marks});" #include inputs for ? when used
INSERT_VAL = f"INSERT INTO {tableName} VALUES ({q_marks})"

GET_ALL_DATA = "SELECT * FROM {tableName};"
GET_ALL_DATA_REV = "SELECT * FROM {tableName} ORDER BY id DESC;"
SORT_BY = "SELECT * FROM {tableName} ORDER BY {field};"
SORT_BY_REV = "SELECT * FROM {tableName} ORDER BY {field} DESC;"

REMOVE_CONTACT = "DELETE FROM can_test_db WHERE id = ?;"

def connect(filename):
    #open data file. if not there, create one
    # os and pathlib are used to create the db file in the same location every
    # time.
    db_file = pkg_resources.resource_filename(
        __name__,
        os.path.join('resources', filename))
    return sqlite3.connect(db_file, 
                           isolation_level=None, 
                           check_same_thread=False)

def create_tables(connection, tablename, columnvalues):
    #context manager, when we create database, it gets saved to the ^^ file
    CREATE_CAN_TABLE = f"""CREATE TABLE IF NOT EXISTS {tableName} 
    ({og_w_type_string});"""

    with connection:
        connection.execute(CREATE_CAN_TABLE)

#given a list of tablenames and each table's column values, create a new table for each
#this would mean changing the create_tables function and the CREATE_CAN_TABLE command

def parseJSON(json_row):
    json_data = []
    for tag in g:
        if tag in json_row:
            json_data.append(json_row[tag])
    
    return tuple(json_data)


def add_row(connection, json_row):
    # Timestamp = row[0]
    # VS15 = row[1]
    # VS19 = row[2]
    # VS33 = row[3]
    # MPPCOV = row[4]
    # MPTC = row[5]
    # MPCT = row[6]
    # with connection:
    #     connection.execute(INSERT_ROW, (Timestamp, VS15, VS19, VS33, MPPCOV, MPTC, MPCT)) #second param has to be tuple
    with connection:
        connection.execute(INSERT_VAL, parseJSON(json_row)) #second param has to be tuple

def get_all_data(connection):
    with connection:
        return connection.execute(GET_ALL_DATA).fetchall()

def sort_by_field(connection, field):
    with connection:
        return connection.execute(SORT_BY.format(field=field)).fetchall()
        #fetch all gives us a list of rows

def reverse_sort_by_field(connection, field):
    if ("Timestamp" in field):
        field = "Timestamp"
    elif ("15VS" in field):
        field = "15VS"
    elif ("19VS" in field):
        field = "19VS"
    elif ("33VS" in field):
        field = "33VS"
    else:
        field = "id"

    with connection:
        return connection.execute(SORT_BY_REV.format(field=field)).fetchall()
        #fetch all gives us a list of rows

def remove_row(connection, id):
    with connection:
        connection.execute(REMOVE_CONTACT, (id,)) #second param has to be tuple
