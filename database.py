"""Database Operations"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file: str = Config.DB_FILE):
        self.db_file = db_file
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_blocked INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT '📁',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coupons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    original_price REAL,
                    stock INTEGER DEFAULT 0,
                    sold_count INTEGER DEFAULT 0,
                    min_purchase INTEGER DEFAULT 1,
                    max_purchase INTEGER DEFAULT 10,
                    is_active INTEGER DEFAULT 1,
                    is_featured INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coupon_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coupon_id INTEGER NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    is_used INTEGER DEFAULT 0,
                    used_by INTEGER,
                    used_at TIMESTAMP,
                    order_id INTEGER,
                    FOREIGN KEY (coupon_id) REFERENCES coupons(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    coupon_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_price REAL NOT NULL,
                    transaction_id TEXT UNIQUE,
                    screenshot_file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    reject_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (coupon_id) REFERENCES coupons(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qr_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    file_id TEXT,
                    upi_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sent_by INTEGER,
                    message TEXT,
                    total_users INTEGER,
                    successful INTEGER,
                    failed INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize QR settings
            cursor.execute("INSERT OR IGNORE INTO qr_settings (id, upi_id) VALUES (1, ?)", (Config.DEFAULT_UPI_ID,))
    
    # USER OPERATIONS
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, first_name, last_name))
                return True
        except:
            return False
    
    def get_all_users(self, active_only: bool = True) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM users"
                if active_only:
                    query += " WHERE is_blocked = 0"
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    # CATEGORY OPERATIONS
    def add_category(self, name: str, description: str = None, icon: str = "📁") -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)", (name, description, icon))
                return cursor.lastrowid
        except:
            return None
    
    def get_categories(self, active_only: bool = True) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT c.*, 
                           (SELECT COUNT(*) FROM coupons WHERE category_id = c.id AND is_active = 1) as coupon_count
                    FROM categories c
                """
                if active_only:
                    query += " WHERE c.is_active = 1"
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def get_category(self, category_id: int) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except:
            return None
    
    def update_category(self, category_id: int, **kwargs) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [category_id]
                cursor.execute(f"UPDATE categories SET {fields} WHERE id = ?", values)
                return True
        except:
            return False
    
    def delete_category(self, category_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                return True
        except:
            return False
    
    # COUPON OPERATIONS
    def add_coupon(self, category_id: int, name: str, price: float, description: str = None, **kwargs) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO coupons (category_id, name, price, description)
                    VALUES (?, ?, ?, ?)
                """, (category_id, name, price, description))
                return cursor.lastrowid
        except:
            return None
    
    def get_coupons(self, category_id: int = None, active_only: bool = True) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT c.*, cat.name as category_name,
                           (SELECT COUNT(*) FROM coupon_codes WHERE coupon_id = c.id AND is_used = 0) as available_stock
                    FROM coupons c
                    LEFT JOIN categories cat ON c.category_id = cat.id
                    WHERE 1=1
                """
                params = []
                if category_id:
                    query += " AND c.category_id = ?"
                    params.append(category_id)
                if active_only:
                    query += " AND c.is_active = 1"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def get_coupon(self, coupon_id: int) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, cat.name as category_name,
                           (SELECT COUNT(*) FROM coupon_codes WHERE coupon_id = c.id AND is_used = 0) as available_stock
                    FROM coupons c
                    LEFT JOIN categories cat ON c.category_id = cat.id
                    WHERE c.id = ?
                """, (coupon_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except:
            return None
    
    def update_coupon(self, coupon_id: int, **kwargs) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [coupon_id]
                cursor.execute(f"UPDATE coupons SET {fields} WHERE id = ?", values)
                return True
        except:
            return False
    
    def delete_coupon(self, coupon_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM coupons WHERE id = ?", (coupon_id,))
                return True
        except:
            return False
    
    # COUPON CODE OPERATIONS
    def add_coupon_codes(self, coupon_id: int, codes: List[str]) -> Tuple[int, int]:
        added = 0
        duplicates = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for code in codes:
                    try:
                        cursor.execute("INSERT INTO coupon_codes (coupon_id, code) VALUES (?, ?)", (coupon_id, code))
                        added += 1
                    except sqlite3.IntegrityError:
                        duplicates += 1
                cursor.execute("UPDATE coupons SET stock = (SELECT COUNT(*) FROM coupon_codes WHERE coupon_id = ?) WHERE id = ?", (coupon_id, coupon_id))
        except Exception as e:
            logger.error(f"Error adding codes: {e}")
        return added, duplicates
    
    def get_available_codes(self, coupon_id: int, quantity: int) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM coupon_codes 
                    WHERE coupon_id = ? AND is_used = 0 
                    LIMIT ?
                """, (coupon_id, quantity))
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    # ORDER OPERATIONS
    def create_order(self, user_id: int, coupon_id: int, quantity: int, total_price: float, transaction_id: str, screenshot_file_id: str = None) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO orders (user_id, coupon_id, quantity, total_price, transaction_id, screenshot_file_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, coupon_id, quantity, total_price, transaction_id, screenshot_file_id))
                return cursor.lastrowid
        except:
            return None
    
    def get_orders(self, user_id: int = None, status: str = None) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT o.*, c.name as coupon_name, u.username
                    FROM orders o
                    LEFT JOIN coupons c ON o.coupon_id = c.id
                    LEFT JOIN users u ON o.user_id = u.user_id
                    WHERE 1=1
                """
                params = []
                if user_id:
                    query += " AND o.user_id = ?"
                    params.append(user_id)
                if status:
                    query += " AND o.status = ?"
                    params.append(status)
                query += " ORDER BY o.created_at DESC"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        return self.get_orders(user_id=user_id)
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT o.*, c.name as coupon_name, u.username
                    FROM orders o
                    LEFT JOIN coupons c ON o.coupon_id = c.id
                    LEFT JOIN users u ON o.user_id = u.user_id
                    WHERE o.id = ?
                """, (order_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except:
            return None
    
    def approve_order(self, order_id: int, user_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                order = self.get_order(order_id)
                if not order:
                    return False
                codes = self.get_available_codes(order['coupon_id'], order['quantity'])
                if len(codes) < order['quantity']:
                    return False
                for code in codes:
                    cursor.execute("""
                        UPDATE coupon_codes 
                        SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP, order_id = ?
                        WHERE id = ?
                    """, (user_id, order_id, code['id']))
                cursor.execute("UPDATE orders SET status = 'delivered', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (order_id,))
                cursor.execute("UPDATE coupons SET sold_count = sold_count + ? WHERE id = ?", (order['quantity'], order['coupon_id']))
                return True
        except:
            return False
    
    def reject_order(self, order_id: int, reason: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = 'rejected', reject_reason = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (reason, order_id))
                return True
        except:
            return False
    
    def get_order_coupon_codes(self, order_id: int) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM coupon_codes WHERE order_id = ?", (order_id,))
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    # QR SETTINGS
    def get_qr_settings(self) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM qr_settings WHERE id = 1")
                row = cursor.fetchone()
                return dict(row) if row else None
        except:
            return None
    
    def update_qr_settings(self, file_id: str = None, upi_id: str = None) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if file_id and upi_id:
                    cursor.execute("UPDATE qr_settings SET file_id = ?, upi_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (file_id, upi_id))
                elif file_id:
                    cursor.execute("UPDATE qr_settings SET file_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (file_id,))
                elif upi_id:
                    cursor.execute("UPDATE qr_settings SET upi_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (upi_id,))
                return True
        except:
            return False
    
    # STATISTICS
    def get_statistics(self) -> Dict[str, Any]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_blocked = 0")
                stats['total_users'] = cursor.fetchone()['count']
                cursor.execute("SELECT COUNT(*) as count FROM categories WHERE is_active = 1")
                stats['total_categories'] = cursor.fetchone()['count']
                cursor.execute("SELECT COUNT(*) as count FROM coupons WHERE is_active = 1")
                stats['total_coupons'] = cursor.fetchone()['count']
                cursor.execute("SELECT COUNT(*) as count FROM orders")
                stats['total_orders'] = cursor.fetchone()['count']
                cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'")
                stats['pending_orders'] = cursor.fetchone()['count']
                cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status IN ('approved', 'delivered')")
                stats['approved_orders'] = cursor.fetchone()['count']
                cursor.execute("SELECT COALESCE(SUM(total_price), 0) as revenue FROM orders WHERE status IN ('approved', 'delivered')")
                stats['total_revenue'] = cursor.fetchone()['revenue']
                cursor.execute("SELECT COUNT(*) as count FROM orders WHERE DATE(created_at) = DATE('now')")
                stats['today_orders'] = cursor.fetchone()['count']
                cursor.execute("SELECT COALESCE(SUM(total_price), 0) as revenue FROM orders WHERE DATE(created_at) = DATE('now') AND status IN ('approved', 'delivered')")
                stats['today_revenue'] = cursor.fetchone()['revenue']
                return stats
        except:
            return {}
    
    # BROADCAST
    def add_broadcast(self, sent_by: int, message: str, total_users: int, successful: int, failed: int) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO broadcasts (sent_by, message, total_users, successful, failed) VALUES (?, ?, ?, ?, ?)", (sent_by, message, total_users, successful, failed))
                return cursor.lastrowid
        except:
            return None

db = Database()