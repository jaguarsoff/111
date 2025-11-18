import sqlite3
from typing import List, Dict, Any
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        phone TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        price_cny REAL,
        weight_kg REAL,
        qty INTEGER,
        category TEXT,
        note TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total_rub REAL,
        status TEXT,
        created_at TEXT,
        contact TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        title TEXT,
        price_cny REAL,
        weight_kg REAL,
        qty INTEGER,
        category TEXT
    )""")
    conn.commit()
    conn.close()

# Cart helpers
def add_to_cart(user_id:int, title:str, price_cny:float, weight_kg:float, qty:int, category:str, note:str=""):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO cart (user_id,title,price_cny,weight_kg,qty,category,note) VALUES (?,?,?,?,?,?,?)",
                (user_id,title,price_cny,weight_kg,qty,category,note))
    conn.commit(); conn.close()

def get_cart(user_id:int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM cart WHERE user_id=?",(user_id,))
    rows = cur.fetchall(); conn.close()
    return [dict(r) for r in rows]

def clear_cart(user_id:int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE user_id=?",(user_id,))
    conn.commit(); conn.close()

def remove_cart_item(item_id:int,user_id:int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id=? AND user_id=?",(item_id,user_id))
    conn.commit(); conn.close()

def update_cart_item_qty(item_id:int,user_id:int,qty:int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE cart SET qty=? WHERE id=? AND user_id=?",(qty,item_id,user_id))
    conn.commit(); conn.close()

# Orders
def create_order_from_cart(user_id:int, total_rub:float, contact:str, created_at:str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO orders (user_id,total_rub,status,created_at,contact) VALUES (?,?,?,?,?)",
                (user_id,total_rub,"new",created_at,contact))
    order_id = cur.lastrowid
    cur.execute("SELECT * FROM cart WHERE user_id=?",(user_id,))
    items = cur.fetchall()
    for it in items:
        cur.execute("INSERT INTO order_items (order_id,title,price_cny,weight_kg,qty,category) VALUES (?,?,?,?,?,?)",
                    (order_id,it["title"],it["price_cny"],it["weight_kg"],it["qty"],it["category"]))
    cur.execute("DELETE FROM cart WHERE user_id=?",(user_id,))
    conn.commit(); conn.close()
    return order_id

def list_orders():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cur.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_order(order_id:int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=?",(order_id,))
    order = cur.fetchone()
    if not order:
        conn.close(); return None
    cur.execute("SELECT * FROM order_items WHERE order_id=?",(order_id,))
    items = cur.fetchall()
    conn.close()
    ret = dict(order)
    ret["items"] = [dict(i) for i in items]
    return ret

def set_order_status(order_id:int, status:str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE orders SET status=? WHERE id=?",(status,order_id))
    conn.commit(); conn.close()

def save_user_contact(user_id:int, username:str, phone:str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (user_id,username,phone) VALUES (?,?,?)",(user_id,username,phone))
    conn.commit(); conn.close()

def get_user(user_id:int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?",(user_id,))
    r = cur.fetchone(); conn.close()
    return dict(r) if r else None
