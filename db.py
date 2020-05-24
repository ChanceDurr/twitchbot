
import psycopg2
import urllib.parse as urlparse
import os
import json, time

url = urlparse.urlparse(os.environ.get("DATABASE_URL"))
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

def connect():
    '''Connects to database, return conn and cursor'''
    conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
                )

    cur = conn.cursor()
    return conn, cur


def commit(conn, cur):
    '''Commits the SQL and closes the connection'''
    cur.close()
    conn.commit()
    conn.close()


### WATCHTIME/POINTS ###
def check_user(name, table, conn=None, cur=None):
    '''Check if name is in table, return true or false'''
    conn, cur = (conn, cur) if conn and cur else connect()
    cur.execute(f"SELECT COUNT(*) FROM {table.lower()} WHERE NAME = '{name.lower()}'")
    result = cur.fetchone()
    commit(conn, cur)
    if result[0] == 1:
        return True
    else:
        return False
    

def add_user(name, table, amount=0, conn=None, cur=None):
    '''Add user to table'''
    conn, cur = (conn, cur) if conn and cur else connect()
    if check_user(name, table):
        print('User already in table')
    else:
        cur.execute(f"INSERT INTO {table.lower()} VALUES('{name.lower()}', {amount})")

    commit(conn, cur)


def get_info(name, table, conn=None, cur=None):
    '''Get stats from table'''
    conn, cur = (conn, cur) if conn and cur else connect()
    if check_user(name, table):
        cur.execute(f"SELECT * FROM {table.lower()} WHERE name = '{name.lower()}'")
        result = cur.fetchone()
    else:
        return 'User not found'

    commit(conn, cur)
    if result[1] is None:
        return 0

    return result[1]


def update_user(name, table, amount: int, conn=None, cur=None):
    '''Add or substract from users stat per table'''
    conn, cur = (conn, cur) if conn and cur else connect()
    if check_user(name, table):
        stat = get_info(name, table) + amount
        if table.lower() == 'watchtime':
            cur.execute(f"UPDATE {table.lower()} SET time = {stat} WHERE name = '{name.lower()}'")
        elif table.lower() == 'points':
            cur.execute(f"UPDATE {table.lower()} SET points = {stat} WHERE name = '{name.lower()}'")
        else:
            return 'Table not found'

    commit(conn, cur)

def get_users(conn=None, cur=None):
    '''Get all users that have watchtime'''
    conn, cur = (conn, cur) if conn and cur else connect()
    cur.execute("SELECT name FROM watchtime")
    result = [x[0] for x in cur.fetchall()]
    commit(conn, cur)
    return result


### COMMANDS ###
def add_command(command_name, command_message, conn=None, cur=None):
    '''Add a simple command'''
    conn, cur = (conn, cur) if conn and cur else connect()
    if check_command(command_name):
        commit(conn, cur)
        return 'Command Exists'
    else:
        cur.execute(f"INSERT INTO commands VALUES('{command_name.lower()}', '{command_message}')")
    commit(conn, cur)


def delete_command(command_name, conn=None, cur=None):
    '''Delete a simple command'''
    conn, cur = (conn, cur) if conn and cur else connect()
    if check_command(check_command):
        cur.execute(f"DELETE FROM commands WHERE name = '{command_name.lower()}'")
    else:
        commit(conn, cur)
        return 'Command Does Not Exist'
    commit(conn, cur)


def check_command(command_name, conn=None, cur=None):
    '''Check to see if a simple command exists'''
    conn, cur = (conn, cur) if conn and cur else connect()
    cur.execute(f"SELECT COUNT(*) FROM commands WHERE name = '{command_name.lower()}'")
    result = cur.fetchone()
    commit(conn, cur)
    if result[0] == 1:
        return True
    else:
        return False
    

def edit_command(command_name, command_message, conn=None, cur=None):
    '''Edit an existing simple command'''
    conn, cur = (conn, cur) if conn and cur else connect()
    if check_command(command_name):
        cur.execute(f"UPDATE commands SET message = '{command_message}' WHERE name = '{command_name.lower()}'")
    commit(conn, cur)


def get_command(command_name, conn=None, cur=None):
    '''Returns command message'''
    conn, cur = (conn, cur) if conn and cur else connect()
    if check_command(command_name):
        cur.execute(f"SELECT * FROM commands WHERE name = '{command_name.lower()}'")

    msg = cur.fetchone()[1]
    commit(conn, cur)
    return msg

def get_all_commands(conn=None, cur=None):
    '''Returns all command names'''
    conn, cur = (conn, cur) if conn and cur else connect()
    cur.execute("SELECT * FROM commands")
    commands = [x[0] for x in cur.fetchall()]
    commit(conn, cur)
    return commands