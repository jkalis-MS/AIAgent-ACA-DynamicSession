"""Simple terminal shell interface for testing agent without DevUI streaming."""
import sys
import asyncio
import uuid
from conversation_storage import create_chat_message_store

async def run_shell_interface_async(agents: dict):
    """Run an interactive terminal shell for chatting with agents (async version)."""
    print("\n" + "="*60)
    print("🐚 Agent Terminal Shell")
    print("="*60)
    print(f"Available agents: {', '.join(agents.keys())}")
    print("\nCommands:")
    print("  /agents  - List available agents")
    print("  /switch <agent-name> - Switch to a different agent")
    print("  /quit    - Exit shell")
    print("="*60 + "\n")
    
    # Select default agent
    agent_names = list(agents.keys())
    if not agent_names:
        print("❌ No agents available!")
        return
    
    current_agent_name = agent_names[0]
    current_agent = agents[current_agent_name]
    
    # Create a session thread_id and message store for this terminal session
    session_thread_id = str(uuid.uuid4())
    message_store = create_chat_message_store(session_thread_id)
    
    print(f"🤖 Using agent: {current_agent_name}")
    print(f"📝 Session ID: {session_thread_id}\n")
    
    while True:
        try:
            # Get user input (use loop.run_in_executor for blocking input)
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, lambda: input("You: ").strip())
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                command = user_input.lower()
                
                if command == "/quit":
                    print("👋 Goodbye!")
                    break
                
                elif command == "/agents":
                    print(f"\nAvailable agents:")
                    for agent_name in agents.keys():
                        marker = "→" if agent_name == current_agent_name else " "
                        print(f"  {marker} {agent_name}")
                    print()
                    continue
                
                elif command.startswith("/switch "):
                    new_agent_name = user_input[8:].strip()
                    if new_agent_name in agents:
                        current_agent_name = new_agent_name
                        current_agent = agents[current_agent_name]
                        print(f"🤖 Switched to: {current_agent_name}\n")
                    else:
                        print(f"❌ Agent '{new_agent_name}' not found. Use /agents to see available agents.\n")
                    continue
                
                else:
                    print(f"❌ Unknown command: {command}\n")
                    continue
            
            # Send message to agent
            print(f"\n🤖 {current_agent_name}: ", end="", flush=True)
            
            try:
                # Run agent asynchronously with message store
                response = await current_agent.run(
                    user_input,
                    message_store=message_store
                )
                
                # Print response
                response_text = str(response) if response else "No response"
                print(response_text)
                print()
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


def run_shell_interface(agents: dict):
    """Synchronous wrapper for the async shell interface."""
    asyncio.run(run_shell_interface_async(agents))

