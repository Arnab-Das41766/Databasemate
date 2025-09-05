#!/usr/bin/env python3
"""
Database Manager for DatabaseMate AI
Handles SQLite database operations with safety checks and beautiful output
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import re

class DatabaseManager:
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        self.console = Console()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize database with sample tables and data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        age INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create products table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        category TEXT,
                        stock INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create orders table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        product_id INTEGER,
                        quantity INTEGER NOT NULL,
                        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (product_id) REFERENCES products (id)
                    )
                ''')
                
                # Insert sample data (only if tables are empty)
                cursor.execute("SELECT COUNT(*) FROM users")
                if cursor.fetchone()[0] == 0:
                    sample_users = [
                        ('Alice Johnson', 'alice@example.com', 28),
                        ('Bob Smith', 'bob@example.com', 35),
                        ('Carol Brown', 'carol@example.com', 22),
                        ('David Wilson', 'david@example.com', 41),
                        ('Eva Davis', 'eva@example.com', 29)
                    ]
                    cursor.executemany("INSERT INTO users (name, email, age) VALUES (?, ?, ?)", sample_users)
                
                cursor.execute("SELECT COUNT(*) FROM products")
                if cursor.fetchone()[0] == 0:
                    sample_products = [
                        ('Laptop', 999.99, 'Electronics', 50),
                        ('Coffee Mug', 12.99, 'Kitchen', 200),
                        ('Book: Python Guide', 29.99, 'Books', 75),
                        ('Wireless Mouse', 25.50, 'Electronics', 120),
                        ('Plant Pot', 8.99, 'Garden', 30)
                    ]
                    cursor.executemany("INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)", sample_products)
                
                cursor.execute("SELECT COUNT(*) FROM orders")
                if cursor.fetchone()[0] == 0:
                    sample_orders = [
                        (1, 1, 1, 'completed'),
                        (2, 2, 2, 'pending'),
                        (1, 3, 1, 'completed'),
                        (3, 1, 1, 'shipped'),
                        (4, 4, 3, 'pending')
                    ]
                    cursor.executemany("INSERT INTO orders (user_id, product_id, quantity, status) VALUES (?, ?, ?, ?)", sample_orders)
                
                conn.commit()
                self.console.print("✅ Database initialized with sample data", style="green")
                
        except Exception as e:
            self.console.print(f"❌ Database initialization error: {e}", style="red")
    
    def is_dangerous_query(self, sql: str) -> Tuple[bool, str]:
        """Check if SQL query is potentially dangerous"""
        sql_upper = sql.upper().strip()
        
        dangerous_operations = [
            ('DROP TABLE', 'This will permanently delete a table and all its data'),
            ('DROP DATABASE', 'This will permanently delete the entire database'),
            ('DELETE FROM', 'This will delete records (potentially all records if no WHERE clause)'),
            ('TRUNCATE', 'This will delete all records from a table'),
            ('ALTER TABLE', 'This will modify table structure')
        ]
        
        for operation, warning in dangerous_operations:
            if operation in sql_upper:
                # Check if DELETE has WHERE clause
                if operation == 'DELETE FROM' and 'WHERE' in sql_upper:
                    continue  # DELETE with WHERE is safer
                return True, warning
        
        return False, ""
    
    def execute_query(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            # Check for dangerous operations
            is_dangerous, warning = self.is_dangerous_query(sql)
            if is_dangerous:
                self.console.print(Panel(
                    f"⚠️  Dangerous Operation Detected!\n\n{warning}\n\nQuery: {sql}", 
                    title="🚨 Safety Warning", 
                    style="red"
                ))
                
                response = self.console.input("\nDo you want to proceed? (yes/no): ").lower()
                if response not in ['yes', 'y']:
                    return {
                        "success": False,
                        "error": "Operation cancelled by user",
                        "cancelled": True
                    }
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # This allows column name access
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # Determine query type
                sql_type = sql.strip().upper().split()[0]
                
                if sql_type in ['SELECT']:
                    results = cursor.fetchall()
                    columns = [description[0] for description in cursor.description] if cursor.description else []
                    
                    return {
                        "success": True,
                        "data": [dict(row) for row in results],
                        "columns": columns,
                        "row_count": len(results),
                        "query_type": "SELECT"
                    }
                
                elif sql_type in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']:
                    affected_rows = cursor.rowcount
                    last_row_id = cursor.lastrowid
                    
                    conn.commit()
                    
                    return {
                        "success": True,
                        "affected_rows": affected_rows,
                        "last_row_id": last_row_id,
                        "query_type": sql_type,
                        "message": f"{sql_type} operation completed successfully"
                    }
                
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported query type: {sql_type}"
                    }
                    
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "sql": sql
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "sql": sql
            }
    
    def display_results(self, result: Dict[str, Any]):
        """Display query results in a beautiful format"""
        if not result["success"]:
            if result.get("cancelled"):
                self.console.print("🚫 Operation cancelled", style="yellow")
            else:
                self.console.print(Panel(
                    f"Error: {result['error']}\nSQL: {result.get('sql', 'N/A')}", 
                    title="❌ Database Error", 
                    style="red"
                ))
            return
        
        if result.get("query_type") == "SELECT":
            if result["row_count"] == 0:
                self.console.print("📭 No results found", style="yellow")
                return
            
            # Create table
            table = Table(title=f"📊 Query Results ({result['row_count']} rows)")
            
            # Add columns
            for column in result["columns"]:
                table.add_column(column, style="cyan")
            
            # Add rows
            for row in result["data"]:
                table.add_row(*[str(row[col]) for col in result["columns"]])
            
            self.console.print(table)
        
        else:
            # Non-SELECT operations
            message = result.get("message", "Operation completed")
            details = []
            
            if "affected_rows" in result:
                details.append(f"Affected rows: {result['affected_rows']}")
            if "last_row_id" in result:
                details.append(f"Last inserted ID: {result['last_row_id']}")
            
            if details:
                message += f"\n{chr(10).join(details)}"
            
            self.console.print(Panel(message, title="✅ Success", style="green"))
    
    def get_schema_info(self) -> str:
        """Get database schema information for the LLM"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = cursor.fetchall()
                
                schema_info = "Database Schema Information:\n\n"
                
                for (table_name,) in tables:
                    schema_info += f"Table: {table_name}\n"
                    
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    for col in columns:
                        col_name, col_type, not_null, default_val, pk = col[1], col[2], col[3], col[4], col[5]
                        constraints = []
                        if pk:
                            constraints.append("PRIMARY KEY")
                        if not_null:
                            constraints.append("NOT NULL")
                        if default_val:
                            constraints.append(f"DEFAULT {default_val}")
                        
                        constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                        schema_info += f"  - {col_name}: {col_type}{constraint_str}\n"
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    schema_info += f"  Rows: {count}\n\n"
                
                return schema_info
                
        except Exception as e:
            return f"Error getting schema: {e}"
    
    def backup_database(self, backup_path: Optional[str] = None):
        """Create a backup of the database"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backup_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.console.print(f"✅ Database backed up to: {backup_path}", style="green")
            return backup_path
        except Exception as e:
            self.console.print(f"❌ Backup failed: {e}", style="red")
            return None

# Test function
def test_database_manager():
    """Test the database manager"""
    console = Console()
    console.print(Panel("🧪 Testing Database Manager", style="bold magenta"))
    
    db = DatabaseManager("data/test_db.db")
    
    # Test queries
    test_queries = [
        "SELECT * FROM users LIMIT 3",
        "SELECT name, email FROM users WHERE age > 25",
        "SELECT p.name, p.price FROM products p WHERE p.category = 'Electronics'",
        "SELECT COUNT(*) as total_users FROM users",
        "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name"
    ]
    
    for query in test_queries:
        console.print(f"\n🔍 Testing: {query}", style="yellow")
        result = db.execute_query(query)
        db.display_results(result)
    
    # Display schema
    console.print("\n📋 Database Schema:", style="blue")
    schema = db.get_schema_info()
    console.print(Panel(schema, title="Database Schema", style="cyan"))

if __name__ == "__main__":
    test_database_manager()
