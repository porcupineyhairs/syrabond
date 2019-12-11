import pymysql
from syrabond import common
from time import sleep


class Mysql:
    """Old-style database handling class. Will be deprecated soon to use ORM."""

    def __init__(self):
        self.write_buffer = set()
        self.read_buffer = set()
        self.cursor_locked = False
        self.buffer_locked = False
        conf = common.extract_config('mysql.json')
        self.debug = bool(conf['debug'])
        self.con = pymysql.connect(conf['host'], conf['user'], conf['password'], conf['database'], connect_timeout=30)
        self.cursor = self.con.cursor()
        conf.clear()

    def rewrite_state(self, uid, state):
        query = 'UPDATE Res_state SET state = \'{}\' WHERE uid = \'{}\''.format(state, uid)
        self.write_cursor(query)

    def rewrite_status(self, uid, status):
        query = 'UPDATE Dev_status SET status = \'{}\' WHERE uid = \'{}\''.format(status, uid)
        self.write_cursor(query)

    def rewrite_quarantine(self, uid, ip):
        query = 'SELECT uid FROM Res_quarantine WHERE uid = \'{}\''.format(uid)
        if self.send_read_query(query):
            query = 'UPDATE Res_quarantine SET ip = \'{}\' WHERE uid = \'{}\''.format(ip, uid)
            self.write_cursor(query)
        else:
            query = 'INSERT INTO Res_quarantine (uid, ip) VALUES (\'{}\', \'{}\')'.format(uid, ip)
            self.send_write_query(query)

    def get_quarantine(self):
        query = 'SELECT uid, ip FROM Res_quarantine'
        return self.send_read_query(query)

    def del_from_quarantine(self, uid):
        query = 'DELETE FROM Res_quarantine WHERE uid = \'{}\''.format(uid)
        self.send_write_query(query)

    def check_state_row_exist(self, uid):
        query = 'SELECT uid FROM Res_state WHERE uid = \'{}\''.format(uid)
        if not self.send_read_query(query):
            self.create_state_row(uid)

    def check_status_row_exist(self, uid):
        query = 'SELECT uid FROM Dev_status WHERE uid = \'{}\''.format(uid)
        if not self.send_read_query(query):
            self.create_status_row(uid)

    def del_resource_rows(self, uid):
        query = 'DELETE FROM Res_state WHERE uid = \'{}\''.format(uid)
        self.send_write_query(query)
        query = 'DELETE FROM Dev_status WHERE uid = \'{}\''.format(uid)
        self.send_write_query(query)

    def create_state_row(self, uid):
        query = 'INSERT INTO Res_state (uid, state) VALUES (\'{}\', \'{}\')'.format(uid, 'None')
        self.send_write_query(query)

    def create_status_row(self, uid):
        query = 'INSERT INTO Dev_status (uid, status) VALUES (\'{}\', \'{}\')'.format(uid, 'None')
        self.send_write_query(query)

    def read_state(self, uid):
        query = 'SELECT state FROM Res_state WHERE uid = \'{}\''.format(uid)
        return self.send_read_query(query)

    def read_status(self, uid):
        query = 'SELECT status FROM Dev_status WHERE uid = \'{}\''.format(uid)
        return self.send_read_query(query)
    
    def send_write_query(self, query):
        if not self.cursor_locked:
            self.write_cursor(query)
        else:
            while self.buffer_locked:
                sleep(0.1)
            self.write_buffer.update({query})
            
    def send_read_query(self, query):
        while self.cursor_locked:
            sleep(0.1)
        return self.read_cursor(query)

    def write_cursor(self, query):
        if not self.con.open:
            self.con.ping(reconnect=True)
        if self.debug:
            print(query)
        self.cursor_locked = True
        if self.write_buffer:
            self.buffer_locked = True
            for query in self.write_buffer:
                self.cursor.execute(query)
            self.con.commit()
            self.write_buffer.clear()
            self.buffer_locked = False
        self.cursor.execute(query)
        result = self.con.commit()
        self.cursor_locked = False
        return result

    def read_cursor(self, query):
        while not self.con.open:
            self.con.ping(reconnect=True)
        if self.debug:
            print(query)
        self.cursor_locked = True
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        self.cursor_locked = False
        return result




