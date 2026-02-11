"""
MCP (Model Context Protocol) + AI Agent Example

This example demonstrates an autonomous AI agent that:
1. Discovers available tools from an MCP server
2. Uses an LLM to decide which tools to use
3. Executes tool calls via MCP
4. Summarizes results for the user

Prerequisites:
1. Install MCP weather server:
   pip install mcp-weather-server

2. Start MCP weather server:
   python3 -m mcp_weather_server \\
     --mode streamable-http \\
     --host localhost \\
     --port 3001 \\
     --stateless

3. Configure Conductor server:
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"

4. Run the example:
   export CONDUCTOR_SERVER_URL="http://localhost:7001/api"
   python examples/agentic_workflows/mcp_weather_agent.py "What's the weather in Tokyo?"

Reference:
https://github.com/conductor-oss/conductor/tree/main/ai#mcp--ai-agent-workflow

MCP Server Installation & Setup:
$ pip install mcp-weather-server
$ python3 -m mcp_weather_server --mode streamable-http --host localhost --port 3001 --stateless

The weather server will be available at: http://localhost:3001/mcp
"""

import os
import sys
from typing import Dict, Any

from conductor.client.configuration.configuration import Configuration
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.task.llm_tasks import (
    ListMcpTools,
    CallMcpTool,
    LlmChatComplete,
    ChatMessage
)


# ══════════════════════════════════════════════════════════════════════════════
# Workflow: MCP AI Agent
# ══════════════════════════════════════════════════════════════════════════════

def create_mcp_agent_workflow(executor: WorkflowExecutor, mcp_server: str) -> ConductorWorkflow:
    """
    Creates an AI agent workflow that uses MCP tools.
    
    Workflow Steps:
    1. List available tools from MCP server
    2. Ask LLM to plan which tool to use based on user request
    3. Execute the tool via MCP
    4. Summarize the result for the user
    
    Args:
        executor: Workflow executor
        mcp_server: MCP server URL (e.g., "http://localhost:3001/mcp")
        
    Returns:
        ConductorWorkflow: Configured MCP agent workflow
    """
    wf = ConductorWorkflow(
        executor=executor,
        name="mcp_ai_agent",
        version=1,
        description="AI agent with MCP tool integration"
    )
    
    # Step 1: Discover available MCP tools
    list_tools = ListMcpTools(
        task_ref_name="discover_tools",
        mcp_server=mcp_server
    )
    
    # Step 2: Ask LLM to plan which tool to use
    plan_task = LlmChatComplete(
        task_ref_name="plan_action",
        llm_provider="anthropic",
        model="claude-sonnet-4-20250514",
        messages=[
            ChatMessage(
                role="system",
                message="""You are an AI agent that can use tools to help users.

Available tools:
${discover_tools.output.tools}

User's request:
${workflow.input.request}

Decide which tool to use and what parameters to pass. Respond with a JSON object:
{
  "method": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  },
  "reasoning": "why you chose this tool and parameters"
}

If no tool is suitable, respond with {"method": "none", "reasoning": "explanation"}."""
            ),
            ChatMessage(
                role="user",
                message="What tool should I use and with what parameters?"
            )
        ],
        temperature=0.1,
        max_tokens=500,
        json_output=True
    )
    
    # Step 3: Execute the selected tool via MCP
    # Note: In a real workflow, you'd use a SWITCH task to handle the "none" case
    execute_tool = CallMcpTool(
        task_ref_name="execute_tool",
        mcp_server=mcp_server,
        method="${plan_action.output.result.method}",
        arguments="${plan_action.output.result.arguments}"  # Arguments dict from LLM planning
    )
    
    # Step 4: Summarize the result
    summarize_task = LlmChatComplete(
        task_ref_name="summarize_result",
        llm_provider="openai",
        model="gpt-4o-mini",
        messages=[
            ChatMessage(
                role="system",
                message="""You are a helpful assistant. Summarize the tool execution result for the user.

Original request: ${workflow.input.request}

Tool used: ${plan_action.output.result.method}
Tool reasoning: ${plan_action.output.result.reasoning}

Tool result: ${execute_tool.output.content}

Provide a natural, conversational response to the user."""
            ),
            ChatMessage(
                role="user",
                message="Please summarize the result"
            )
        ],
        temperature=0.3,
        max_tokens=300
    )
    
    # Build workflow
    wf >> list_tools >> plan_task >> execute_tool >> summarize_task
    
    return wf


def create_simple_weather_workflow(executor: WorkflowExecutor, mcp_server: str) -> ConductorWorkflow:
    """
    Creates a simple weather query workflow (no planning, direct tool call).
    
    Args:
        executor: Workflow executor
        mcp_server: MCP server URL
        
    Returns:
        ConductorWorkflow: Simple weather workflow
    """
    wf = ConductorWorkflow(
        executor=executor,
        name="simple_weather_query",
        version=1,
        description="Simple weather query via MCP"
    )
    
    # Direct weather query
    get_weather = CallMcpTool(
        task_ref_name="get_weather",
        mcp_server=mcp_server,
        method="get_current_weather",
        arguments={
            "city": "${workflow.input.city}"
        }
    )
    
    wf >> get_weather
    
    return wf


# ══════════════════════════════════════════════════════════════════════════════
# Main: Run MCP Agent
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python mcp_weather_agent.py <request> [--simple]")
        print("\nExamples:")
        print('  python mcp_weather_agent.py "What\'s the weather in Tokyo?"')
        print('  python mcp_weather_agent.py "Temperature in New York" --simple')
        print("\nPrerequisites:")
        print("1. Install: pip install mcp-weather-server")
        print("2. Start server:")
        print("   python3 -m mcp_weather_server --mode streamable-http --host localhost --port 3001 --stateless")
        sys.exit(1)
    
    request = sys.argv[1]
    simple_mode = "--simple" in sys.argv
    
    # Configuration
    server_url = os.getenv('CONDUCTOR_SERVER_URL', 'http://localhost:7001/api')
    mcp_server = os.getenv('MCP_SERVER_URL', 'http://localhost:3001/mcp')
    
    configuration = Configuration(
        server_api_url=server_url,
        debug=False
    )
    
    clients = OrkesClients(configuration=configuration)
    executor = clients.get_workflow_executor()
    
    print("=" * 80)
    print("MCP AI AGENT - Tool Integration Example")
    print("=" * 80)
    print(f"\n🤖 Mode: {'Simple Weather Query' if simple_mode else 'AI Agent with Planning'}")
    print(f"📡 MCP Server: {mcp_server}")
    print(f"💬 Request: {request}\n")
    
    try:
        # Create and register workflow
        if simple_mode:
            # Parse city from request  
            # Look for city name after common prepositions
            import re
            match = re.search(r'\b(?:in|at|for|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', request)
            if match:
                city = match.group(1)
            else:
                # Fallback: look for capitalized words
                words = [w for w in request.split() if w and w[0].isupper()]
                city = words[-1] if words else "San Francisco"
            
            city = city.strip('?".,')
            
            print("📋 Creating simple weather workflow...")
            wf = create_simple_weather_workflow(executor, mcp_server)
            wf.register(overwrite=True)
            print(f"✅ Workflow registered: {wf.name}")
            print(f"🌍 Extracted city: {city}")
            
            workflow_input = {
                "city": city
            }
        else:
            print("📋 Creating MCP AI agent workflow...")
            wf = create_mcp_agent_workflow(executor, mcp_server)
            wf.register(overwrite=True)
            print(f"✅ Workflow registered: {wf.name}")
            
            workflow_input = {
                "request": request
            }
        
        # Execute workflow
        print(f"\n🚀 Starting workflow execution...")
        workflow_run = wf.execute(
            workflow_input=workflow_input,
            wait_for_seconds=30
        )
        
        workflow_id = workflow_run.workflow_id
        status = workflow_run.status
        
        print(f"📊 Workflow Status: {status}")
        print(f"🔗 Workflow ID: {workflow_id}")
        print(f"🌐 View: {server_url.replace('/api', '')}/execution/{workflow_id}")
        
        if status == "COMPLETED":
            # Display results
            print("\n" + "=" * 80)
            print("RESULTS")
            print("=" * 80)
            
            output = workflow_run.output
            
            if simple_mode:
                # Simple weather output (output is directly the MCP tool result)
                if "content" in output:
                    for item in output["content"]:
                        if item.get("type") == "text":
                            print(f"\n🌤️  {item['text']}\n")
            else:
                # AI agent output
                
                # Tools discovered
                if "discover_tools" in output and "tools" in output["discover_tools"]:
                    tools = output["discover_tools"]["tools"]
                    print(f"\n🔧 Tools Available: {len(tools)}")
                    for tool in tools:
                        print(f"  • {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
                
                # Agent's plan
                if "plan_action" in output and "result" in output["plan_action"]:
                    plan = output["plan_action"]["result"]
                    print(f"\n🧠 Agent's Plan:")
                    print(f"  Tool: {plan.get('method', 'unknown')}")
                    print(f"  Arguments: {plan.get('arguments', {})}")
                    print(f"  Reasoning: {plan.get('reasoning', 'none provided')}")
                
                # Tool execution result
                if "execute_tool" in output:
                    tool_result = output["execute_tool"]
                    print(f"\n⚙️  Tool Execution:")
                    if "content" in tool_result:
                        for item in tool_result["content"]:
                            if item.get("type") == "text":
                                print(f"  {item['text']}")
                    print(f"  Error: {tool_result.get('isError', False)}")
                
                # Final summary
                if "summarize_result" in output:
                    summary = output["summarize_result"].get("result", "No summary generated")
                    print(f"\n💬 Agent's Response:")
                    print(f"\n{summary}\n")
                    
                    # Token usage
                    for task in ["plan_action", "summarize_result"]:
                        if task in output and "metadata" in output[task]:
                            metadata = output[task]["metadata"]
                            if "usage" in metadata:
                                usage = metadata["usage"]
                                print(f"📊 {task} tokens: {usage.get('totalTokens', 0)}")
        
        else:
            print(f"\n❌ Workflow failed with status: {status}")
            if hasattr(workflow_run, 'reason_for_incompletion'):
                print(f"Reason: {workflow_run.reason_for_incompletion}")
            
            # Show task failures
            if hasattr(workflow_run, 'tasks'):
                failed_tasks = [t for t in workflow_run.tasks if t.status == "FAILED"]
                if failed_tasks:
                    print("\n❌ Failed Tasks:")
                    for task in failed_tasks:
                        ref_name = getattr(task, 'reference_task_name', getattr(task, 'taskReferenceName', 'unknown'))
                        reason = getattr(task, 'reason_for_incompletion', getattr(task, 'reasonForIncompletion', 'No reason provided'))
                        print(f"  • {ref_name}: {reason}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
