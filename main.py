#!/usr/bin/env python3
"""
DatabaseMate AI: Natural Language Database Assistant
Main program that combines LLM and Database components
"""
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.layout import Layout
from rich.live import Live
import time

# Import our custom modules
from llm_client import LLMClient
from database_manager import DatabaseManager

class DatabaseMateAI:
    def __init__(self, db_path: str = "data/database.db"):
        self.console = Console()
        self.db_manager = DatabaseManager(db_path)
        self.llm_client = LLMClient()
        self.session_queries = []
        
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = """
🤖 Welcome to DatabaseMate AI!

I'm your natural language database assistant. You can:
• Ask questions about your data in plain English
• Request reports and analytics
• Create, update, or delete records
• Get database insights and summaries

Examples:
• "Show me all users older than 25"
• "How many orders were placed this week?"
• "Add a new user named John with email john@example.com"
• "What's the total revenue from electronics?"

Type 'help' for commands, 'quit' to exit.
        """
        
        self.console.print(Panel(
            welcome_text,
            title="🚀 DatabaseMate AI v1.0",
            style="bold blue"
        ))
    
    def display_help(self):
        """Display help information"""
        help_text = """
📋 Available Commands:

🔍 Natural Language Queries:
  Just type your question in plain English!
  
📊 Special Commands:
  • help         - Show this help message
  • schema       - Display database structure
  • history      - Show recent queries
  • clear        - Clear conversation history
  • backup       - Create database backup
  • stats        - Show database statistics
  • quit/exit    - Exit the program

💡 Query Examples:
  • "List all products under $50"
  • "Show users who haven't placed orders"
  • "Create a table for customers"
  • "Update Bob's age to 36"
  • "Delete orders older than 30 days"

⚠️  Safety Features:
  • Dangerous operations require confirmation
  • Automatic backups before major changes
  • Query validation and error handling
        """
        
        self.console.print(Panel(help_text, title="📚 Help Guide", style="green"))
    
    def display_stats(self):
        """Display database statistics"""
        try:
            stats = []
            
            # Get table counts
            tables = ['users', 'products', 'orders']
            for table in tables:
                result = self.db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                if result["success"]:
                    count = result["data"][0]["count"]
                    stats.append(f"📊 {table.capitalize()}: {count} records")
            
            # Get recent activity
            recent_orders = self.db_manager.execute_query("SELECT COUNT(*) as count FROM orders WHERE date(order_date) = date('now')")
            if recent_orders["success"]:
                today_orders = recent_orders["data"][0]["count"]
                stats.append(f"📅 Orders today: {today_orders}")
            
            # Database size
            db_size = os.path.getsize(self.db_manager.db_path) / 1024  # KB
            stats.append(f"💾 Database size: {db_size:.1f} KB")
            
            stats_text = "\n".join(stats)
            self.console.print(Panel(stats_text, title="📈 Database Statistics", style="cyan"))
            
        except Exception as e:
            self.console.print(f"❌ Error getting statistics: {e}", style="red")
    
    def display_history(self):
        """Display recent query history"""
        if not self.session_queries:
            self.console.print("📭 No queries in current session", style="yellow")
            return
        
        self.console.print(Panel(
            "\n".join([f"{i+1}. {query}" for i, query in enumerate(self.session_queries[-10:])]),
            title="📜 Recent Queries (Last 10)",
            style="magenta"
        ))
    
    def process_natural_language_query(self, user_input: str):
        """Process a natural language query"""
        # Add schema context to help the LLM
        schema_info = self.db_manager.get_schema_info()
        self.llm_client.add_table_context(schema_info)
        
        # Get SQL from LLM
        self.console.print("🧠 Converting to SQL...", style="blue")
        llm_result = self.llm_client.natural_language_to_sql(user_input)
        
        if not llm_result["success"]:
            self.console.print(f"❌ AI Error: {llm_result['error']}", style="red")
            return
        
        sql_query = llm_result["sql"]
        
        # Display the generated SQL
        self.console.print(Panel(
            sql_query,
            title="🔍 Generated SQL",
            style="yellow"
        ))
        
        # Ask for confirmation for dangerous operations
        is_dangerous, warning = self.db_manager.is_dangerous_query(sql_query)
        if is_dangerous:
            self.console.print(f"⚠️  Warning: {warning}", style="red")
            confirm = Prompt.ask("Execute this query?", choices=["yes", "no"], default="no")
            if confirm.lower() != "yes":
                self.console.print("🚫 Query cancelled", style="yellow")
                return
        
        # Execute the query
        self.console.print("⚡ Executing query...", style="green")
        db_result = self.db_manager.execute_query(sql_query)
        
        # Display results
        self.db_manager.display_results(db_result)
        
        # Add to session history
        self.session_queries.append(user_input)
        
        # Show AI explanation if different from SQL
        if llm_result["explanation"] != sql_query and len(llm_result["explanation"]) > len(sql_query) + 20:
            self.console.print(Panel(
                llm_result["explanation"],
                title="💡 AI Explanation",
                style="blue"
            ))
    
    def handle_command(self, command: str):
        """Handle special commands"""
        command = command.lower().strip()
        
        if command in ['help', 'h']:
            self.display_help()
        elif command in ['schema', 's']:
            schema = self.db_manager.get_schema_info()
            self.console.print(Panel(schema, title="🗃️ Database Schema", style="cyan"))
        elif command in ['history', 'hist']:
            self.display_history()
        elif command in ['clear', 'cls']:
            self.llm_client.clear_history()
            self.session_queries = []
            self.console.print("🧹 Session cleared", style="green")
        elif command in ['backup', 'b']:
            backup_path = self.db_manager.backup_database()
            if backup_path:
                self.console.print(f"💾 Backup created: {backup_path}", style="green")
        elif command in ['stats', 'statistics']:
            self.display_stats()
        elif command in ['quit', 'exit', 'q']:
            return False
        else:
            self.console.print(f"❓ Unknown command: {command}. Type 'help' for available commands.", style="yellow")
        
        return True
    
    def run(self):
        """Main application loop"""
        # Check if Ollama is available
        if not self.llm_client.is_server_available():
            self.console.print("❌ Ollama server not available. Please start Ollama first.", style="red")
            self.console.print("Run: ollama serve", style="yellow")
            return
        
        # Display welcome message
        self.display_welcome()
        
        # Main interaction loop
        try:
            while True:
                # Get user input
                user_input = Prompt.ask("\n🤖 DatabaseMate", default="").strip()
                
                if not user_input:
                    continue
                
                # Check if it's a command
                if user_input.startswith('/') or user_input.lower() in ['help', 'quit', 'exit', 'schema', 'history', 'clear', 'backup', 'stats']:
                    command = user_input.lstrip('/')
                    if not self.handle_command(command):
                        break
                else:
                    # Process as natural language query
                    self.process_natural_language_query(user_input)
                    
        except KeyboardInterrupt:
            self.console.print("\n👋 Goodbye!", style="green")
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e}", style="red")

# Configuration loading
def load_config():
    """Load configuration (placeholder for future config file)"""
    return {
        "db_path": "data/database.db",
        "llm_model": "qwen2.5-coder:7b",
        "ollama_url": "http://localhost:11434"
    }

# Main entry point
def main():
    """Main entry point"""
    try:
        # Load configuration
        config = load_config()
        
        # Create and run the application
        app = DatabaseMateAI(config["db_path"])
        app.run()
        
    except Exception as e:
        console = Console()
        console.print(f"❌ Failed to start DatabaseMate AI: {e}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    main()
