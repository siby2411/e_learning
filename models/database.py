#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os

class Database:
    def __init__(self):
        self.conn = None

    def connect(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cours.db')
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def execute(self, query, params=()):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid

    def fetch_one(self, query, params=()):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query, params=()):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

db = Database()
