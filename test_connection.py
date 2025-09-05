#!/usr/bin/env python3
"""
Test connection to Ollama server
"""
import requests
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def test_ollama():
    console.print(Panel("🧪 Testing Ollama Connection", style="blue"))
    
    try:
        # Test if Ollama server is running
        console.print("📡 Checking if Ollama server is running...")
        
        # First, let's check if the server is accessible
        response = requests.get('http://localhost:11434/', timeout=5)
        
        if response.status_code == 200:
            console.print("✅ Ollama server is running!", style="green")
        else:
            console.print(f"⚠️  Ollama server responded with status: {response.status_code}", style="yellow")
            
        # Test if our model is available
        console.print("🤖 Testing model availability...")
        
        response = requests.post('http://localhost:11434/api/generate', 
                               json={
                                   'model': 'qwen2.5-coder:7b',
                                   'prompt': 'Convert this to SQL: show all users',
                                   'stream': False
                               },
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            console.print("✅ Model is working!", style="green")
            console.print(Panel(f"AI Response: {result['response']}", title="🤖 AI Output", style="green"))
            return True
        else:
            console.print(f"❌ Model request failed: {response.status_code}", style="red")
            console.print(f"Response: {response.text}", style="red")
            return False
            
    except requests.exceptions.ConnectionError:
        console.print("❌ Cannot connect to Ollama server!", style="red")
        console.print("💡 Make sure Ollama is running: `ollama serve`", style="yellow")
        return False
    except requests.exceptions.Timeout:
        console.print("⏰ Request timed out. Model might still be downloading.", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        return False

def check_model_status():
    """Check if the model is downloaded"""
    console.print("📋 Checking available models...")
    
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("Available models:", style="blue")
            console.print(result.stdout)
            
            if 'qwen2.5-coder:7b' in result.stdout:
                console.print("✅ qwen2.5-coder:7b is available!", style="green")
                return True
            else:
                console.print("⚠️  qwen2.5-coder:7b not found. Still downloading?", style="yellow")
                return False
        else:
            console.print(f"❌ Error checking models: {result.stderr}", style="red")
            return False
            
    except Exception as e:
        console.print(f"❌ Error running ollama list: {e}", style="red")
        return False

if __name__ == "__main__":
    console.print(Panel("🚀 DatabaseMate AI - Connection Test", style="bold magenta"))
    
    # Check model status first
    model_available = check_model_status()
    
    if model_available:
        # Test the connection
        success = test_ollama()
        
        if success:
            console.print(Panel("🎉 Everything is working! Ready to build DatabaseMate AI!", style="bold green"))
        else:
            console.print(Panel("❌ Connection test failed. Check the errors above.", style="bold red"))
    else:
        console.print(Panel("⏳ Model not ready yet. Wait for download to complete.", style="bold yellow"))
