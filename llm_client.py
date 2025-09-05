#!/usr/bin/env python3
"""
LLM Client for DatabaseMate AI
Handles communication with local Ollama instance for natural language to SQL conversion
"""

import requests
import json
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import time

class LLMClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"):
        self.base_url = base_url
        self.model = model
        self.console = Console()
        self.conversation_history = []
        
        # System prompt that teaches the LLM about SQL generation
        self.system_prompt = """You are DatabaseMate AI, an expert SQL assistant. Your job is to convert natural language into SQLite queries.

IMPORTANT RULES:
1. ALWAYS respond with valid SQLite syntax
2. For SELECT queries, return just the SQL
3. For INSERT/UPDATE/DELETE, return SQL with placeholders (?) for values when needed
4. If you need table structure info, ask for it
5. Be conversational but focus on SQL generation
6. Remember previous context in our conversation
7. For dangerous operations (DROP, DELETE), ask for confirmation

COMMON PATTERNS:
- "show/list/display/get" → SELECT
- "add/insert/create record" → INSERT  
- "update/change/modify" → UPDATE
- "delete/remove" → DELETE
- "create table" → CREATE TABLE
- "drop/delete table" → DROP TABLE

EXAMPLES:
Human: "Add a user named John with email john@example.com age 25"
You: INSERT INTO users (name, email, age) VALUES ('John', 'john@example.com', 25);
"""

    def is_server_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def query_llm(self, user_message: str, include_context: bool = True) -> Optional[str]:
        """
        Send a query to the LLM and get SQL response
        """
        try:
            # Build the conversation context
            messages = []
            
            # Add system prompt
            if include_context:
                messages.append({"role": "system", "content": self.system_prompt})
                
                # Add conversation history
                for msg in self.conversation_history[-6:]:  # Keep last 6 messages
                    messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Make API call
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["message"]["content"]
                
                # Store in conversation history
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                return ai_response
            else:
                self.console.print(f"❌ API Error: {response.status_code}", style="red")
                return None
                
        except requests.exceptions.Timeout:
            self.console.print("⏰ Request timed out", style="yellow")
            return None
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")
            return None
    
    def extract_sql(self, ai_response: str) -> Optional[str]:
        """
        Extract SQL query from AI response
        """
        # Look for SQL code blocks
        if "```sql" in ai_response:
            start = ai_response.find("```sql") + 6
            end = ai_response.find("```", start)
            if end != -1:
                return ai_response[start:end].strip()
        
        # Look for SQL statements (simple heuristic)
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                return line
        
        return ai_response.strip()
    
    def natural_language_to_sql(self, user_input: str) -> Dict[str, Any]:
        """
        Convert natural language to SQL query
        Returns dict with SQL, explanation, and metadata
        """
        self.console.print(f"🧠 Processing: '{user_input}'", style="blue")
        
        # Enhanced prompt that asks for both SQL and values
        enhanced_prompt = f"""
        {user_input}
        
        Please provide:
        1. The SQL query with actual values (no placeholders like ?)
        2. Use single quotes for text values
        3. Extract all values from the natural language input
        
        For example:
        - "add user named John with email john@test.com age 25" → INSERT INTO users (name, email, age) VALUES ('John', 'john@test.com', 25);
        - "show users older than 30" → SELECT * FROM users WHERE age > 30;
        """
        
        # Query the LLM
        ai_response = self.query_llm(enhanced_prompt)
        
        if not ai_response:
            return {
                "success": False,
                "error": "Failed to get response from AI"
            }
        
        # Extract SQL from response
        sql_query = self.extract_sql(ai_response)
        
        return {
            "success": True,
            "sql": sql_query,
            "explanation": ai_response,
            "original_query": user_input
        }
    
    def add_table_context(self, table_info: str):
        """Add database table structure to conversation context"""
        context_msg = f"Database schema information:\n{table_info}"
        self.conversation_history.append({
            "role": "system", 
            "content": context_msg
        })
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.console.print("🧹 Conversation history cleared", style="green")
    
    def display_response(self, result: Dict[str, Any]):
        """Display AI response in a nice format"""
        if result["success"]:
            self.console.print(Panel(
                result["sql"], 
                title="🔍 Generated SQL", 
                style="green"
            ))
            
            if result["explanation"] != result["sql"]:
                self.console.print(Panel(
                    result["explanation"], 
                    title="💡 AI Explanation", 
                    style="blue"
                ))
        else:
            self.console.print(Panel(
                result.get("error", "Unknown error"), 
                title="❌ Error", 
                style="red"
            ))

# Test function
def test_llm_client():
    """Test the LLM client"""
    console = Console()
    console.print(Panel("🧪 Testing LLM Client", style="bold magenta"))
    
    client = LLMClient()
    
    # Test queries
    test_queries = [
        "Show me all users",
        "Find users with age greater than 25",
        "Add a user named TestUser with email test@example.com age 30",
        "How many orders were placed today?"
    ]
    
    for query in test_queries:
        console.print(f"\n🔍 Testing: '{query}'", style="yellow")
        result = client.natural_language_to_sql(query)
        client.display_response(result)
        time.sleep(1)  # Pause between queries

if __name__ == "__main__":
    test_llm_client()
