##
# Part of `MasterNodeMonitorBot`
#
# Copyright 2018 dustinface
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

import logging
from stashpay.util import ThreadedSQLite
import threading
import sqlite3 as sql

logger = logging.getLogger("database")

#####
#
# Wrapper for the user database where all the users
# and their added nodes are stored.
#
#####

class BotDatabase(object):

    def __init__(self, dburi):

        self.connection = ThreadedSQLite(dburi)

        if self.isEmpty():
            self.reset()

    def isEmpty(self):

        tables = []

        with self.connection as db:

            db.cursor.execute("SELECT name FROM sqlite_master")

            tables = db.cursor.fetchall()

        return len(tables) == 0

    def addUser(self, userId, userName):

        user = self.getUser(userId)

        if user == None:

            if userName == None or userName == '':
                userName = 'Unknown'

            with self.connection as db:

                logger.debug("addUser: New user {} {}".format(userId,userName))

                db.cursor.execute("INSERT INTO users( id, name, status_n, timeout_n, reward_n, network_n  ) values( ?, ?, 1, 1, 1, 0 )", ( userId, userName ))

                user = db.cursor.lastrowid

        else:

            user = user['id']

        return user

    def addNode(self, collateral,name,userId,userName):

        collateral = str(collateral)

        user = self.addUser(userId, userName)
        node = self.getNodes(collateral, user)

        if node == None or node['user_id'] != user:

            with self.connection as db:

                db.cursor.execute("INSERT INTO nodes( collateral, name, user_id  )  values( ?, ?, ? )", ( collateral, name, user ) )

                return True

        return False

    def getUsers(self, condition = None ):

        users = []

        with self.connection as db:
            query = "SELECT * FROM users"

            if condition:
                query += (' ' + condition)

            db.cursor.execute(query)
            users = db.cursor.fetchall()

        return users

    def getUser(self, userId):

        user = None

        with self.connection as db:

            db.cursor.execute("SELECT * FROM users WHERE id=?",[userId])

            user = db.cursor.fetchone()

        return user

    def getAllNodes(self, userId = None):

        nodes = []

        with self.connection as db:

            if userId:
                db.cursor.execute("SELECT * FROM nodes WHERE user_id=? ORDER BY name",[userId])
            else:
                db.cursor.execute("SELECT * FROM nodes")

            nodes = db.cursor.fetchall()

        return nodes

    def getNodes(self, collateral, userId = None):

        nodes = None

        collateral = str(collateral)

        with self.connection as db:

            if userId:
                db.cursor.execute("SELECT * FROM nodes WHERE collateral=? and user_id=?",(str(collateral),userId))
                nodes = db.cursor.fetchone()
            else:
                db.cursor.execute("SELECT * FROM nodes WHERE collateral=?",[str(collateral)])
                nodes = db.cursor.fetchall()

        return nodes

    def updateUsername(self, name, userId):

        with self.connection as db:

            db.cursor.execute("UPDATE users SET name=? WHERE id=?",(name,userId))

    def updateNode(self, collateral, userId, name):

        collateral = str(collateral)

        with self.connection as db:

            db.cursor.execute("UPDATE nodes SET name=? WHERE collateral=? and user_id=?",(name, str(collateral), userId))

    def updateStatusNotification(self, userId, state):

        with self.connection as db:

            db.cursor.execute("UPDATE users SET status_n = ? WHERE id=?",(state,userId))

    def updateTimeoutNotification(self, userId, state):

        with self.connection as db:

            db.cursor.execute("UPDATE users SET timeout_n = ? WHERE id=?",(state,userId))

    def updateRewardNotification(self, userId, state):

        with self.connection as db:

            db.cursor.execute("UPDATE users SET reward_n = ? WHERE id=?",(state,userId))

    def updateNetworkNotification(self, userId, state):

        with self.connection as db:

            db.cursor.execute("UPDATE users SET network_n = ? WHERE id=?",(state,userId))

    def deleteUser(self, userId):

        with self.connection as db:

            db.cursor.execute("DELETE FROM users WHERE id=?",[userId])

    def deleteNode(self, collateral, userId):

        with self.connection as db:

            db.cursor.execute("DELETE FROM nodes WHERE collateral=? and user_id=?",(str(collateral),userId))

    def deleteNodesForUser(self, userId):

        with self.connection as db:
            db.cursor.execute("DELETE FROM nodes WHERE user_id=?",[userId])

    def deleteNodesWithId(self, collateral):

        collateral = str(collateral)

        with self.connection as db:
            db.cursor.execute("DELETE FROM nodes WHERE collateral=?",[str(collateral)])

    def reset(self):

        sql = 'BEGIN TRANSACTION;\
        CREATE TABLE "users" (\
        	`id`	INTEGER NOT NULL PRIMARY KEY,\
        	`name`	INTEGER,\
        	`status_n`	INTEGER,\
        	`reward_n`	INTEGER,\
        	`timeout_n`	INTEGER,\
        	`network_n` INTEGER,\
            `detail_n` INTEGER,\
            `last_activity`	INTEGER\
        );\
        CREATE TABLE "nodes" (\
        	`id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
        	`user_id` INTEGER,\
        	`collateral` STRING NOT NULL,\
        	`name` TEXT NOT NULL\
        );\
        CREATE INDEX `node_id` ON `nodes` (`collateral` );\
        CREATE INDEX `node_user` ON `nodes` (`user_id` );\
        COMMIT;'

        with self.connection as db:
            db.cursor.executescript(sql)


#####
#
# Wrapper for the node database where all the nodes from the
# global nodelist are stored.
#
#####

class NodeDatabase(object):

    def __init__(self, dburi):

        self.connection = ThreadedSQLite(dburi)

        if self.isEmpty():
            self.reset()

    def isEmpty(self):

        tables = []

        with self.connection as db:

            db.cursor.execute("SELECT name FROM sqlite_master")

            tables = db.cursor.fetchall()

        return len(tables) == 0

    def raw(self, query):

        with self.connection as db:
            db.cursor.execute(query)
            return db.cursor.fetchall()

        return None


    def addNode(self, collateral, node):

        try:

            with self.connection as db:
                query = "INSERT INTO nodes(\
                        collateral,\
                        collateral_block,\
                        payee, \
                        status,\
                        activeseconds,\
                        last_paid_block,\
                        last_paid_time,\
                        last_seen,\
                        protocol,\
                        ip,\
                        timeout ) \
                        values( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )"

                db.cursor.execute(query, (
                                  str(collateral),
                                  collateral.block,
                                  node.payee,
                                  node.status,
                                  node.activeSeconds,
                                  node.lastPaidBlock,
                                  node.lastPaidTime,
                                  node.lastSeen,
                                  node.protocol,
                                  node.ip,
                                  node.timeout))

                return db.cursor.lastrowid

        except Exception as e:
            logger.debug("Duplicate?!", exc_info=e)

        return None

    def getNodes(self, filter = None):

        nodes = []
        rows = '*' if filter == None else ",".join(filter)

        with self.connection as db:

            db.cursor.execute("SELECT {} FROM nodes".format(rows))

            nodes = db.cursor.fetchall()

        return nodes

    def getNodeCount(self, where = None):

        count = 0

        with self.connection as db:

            if where:
                db.cursor.execute("SELECT COUNT(collateral) FROM nodes WHERE {}".format(where))
            else:
                db.cursor.execute("SELECT COUNT(collateral) FROM nodes")

            count = db.cursor.fetchone()[0]

        return count

    def getNodeByIp(self, ip):

        node = None

        search = "{}:9999".format(ip)

        with self.connection as db:

            db.cursor.execute("SELECT * FROM nodes WHERE ip=?",[search])

            node = db.cursor.fetchone()

        return node

    def getNodesByPayee(self, payee):

        nodes = None

        with self.connection as db:

            db.cursor.execute("SELECT * FROM nodes WHERE payee=?",[payee])

            nodes = db.cursor.fetchall()

        return nodes if nodes else []

    def updateNode(self, collateral, node):

        if not self.addNode(collateral, node):

            with self.connection as db:

                query = "UPDATE nodes SET\
                                collateral_block=?,\
                                payee=?,\
                                status=?,\
                                activeseconds=?,\
                                last_paid_block=?,\
                                last_paid_time=?,\
                                last_seen=?,\
                                protocol=?,\
                                ip=?,\
                                timeout=?\
                                WHERE collateral=?"

                db.cursor.execute(query, (\
                                  collateral.block,\
                                  node.payee,\
                                  node.status,\
                                  node.activeSeconds,\
                                  node.lastPaidBlock,\
                                  node.lastPaidTime,\
                                  node.lastSeen,\
                                  node.protocol,\
                                  node.ip,
                                  node.timeout,
                                  str(collateral)))

    def deleteNode(self, collateral):

        with self.connection as db:

            db.cursor.execute("DELETE FROM nodes WHERE collateral=?",[str(collateral)])

    def reset(self):

        sql = '\
        BEGIN TRANSACTION;\
        CREATE TABLE "nodes" (\
        	`collateral` TEXT NOT NULL PRIMARY KEY,\
            `collateral_block` INTEGER,\
        	`payee`	TEXT,\
        	`status` TEXT,\
        	`activeseconds`	INTEGER,\
        	`last_paid_block` INTEGER,\
        	`last_paid_time` INTEGER,\
        	`last_seen`	INTEGER,\
        	`protocol`	INTEGER,\
            `timeout` INTEGER,\
        	`ip` TEXT\
        );\
        COMMIT;'

        with self.connection as db:
            db.cursor.executescript(sql)
