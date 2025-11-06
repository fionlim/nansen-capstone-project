import streamlit as st
import json
from typing import Optional, Dict, Any, List, Generator
import httpx
from openai import OpenAI


class NansenMCPClient:
    """Custom MCP client for Nansen HTTP-based MCP server."""

    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.session_id: Optional[str] = None
        self.tools: List[Dict[str, Any]] = []
        self._initialized = False

    def _parse_sse_response(self, text: str) -> Dict[str, Any]:
        """Parse Server-Sent Events format response."""
        if text.startswith("event:"):
            lines = text.strip().split('\n')
            for line in lines:
                if line.startswith("data: "):
                    json_data = line[6:]  # Remove "data: " prefix
                    return json.loads(json_data)
        return json.loads(text)

    def _parse_sse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single SSE line."""
        if line.startswith("data: "):
            try:
                json_data = line[6:]  # Remove "data: " prefix
                return json.loads(json_data)
            except json.JSONDecodeError:
                return None
        return None

    def initialize(self) -> bool:
        """Initialize the MCP session."""
        if self._initialized:
            return True

        headers = {
            "NANSEN-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {
                    "name": "streamlit-nansen-chat",
                    "version": "1.0.0"
                }
            }
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                # Initialize session
                response = client.post(self.server_url, json=init_payload, headers=headers)

                if response.status_code != 200:
                    raise Exception(f"Failed to initialize: {response.text}")

                # Parse response (validation)
                self._parse_sse_response(response.text)

                # Extract session ID
                self.session_id = response.headers.get('mcp-session-id')
                if self.session_id:
                    headers['mcp-session-id'] = self.session_id

                # Send initialized notification
                initialized_payload = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                client.post(self.server_url, json=initialized_payload, headers=headers)

                # List available tools
                tools_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                tools_response = client.post(self.server_url, json=tools_payload, headers=headers)
                if tools_response.status_code == 200:
                    tools_result = self._parse_sse_response(tools_response.text)
                    self.tools = tools_result.get('result', {}).get('tools', [])

                self._initialized = True
                return True

        except Exception as e:
            raise Exception(f"MCP initialization failed: {str(e)}")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool (non-streaming version for backward compatibility)."""
        result_parts = []
        for chunk in self.call_tool_streaming(tool_name, arguments):
            if isinstance(chunk, str):
                result_parts.append(chunk)
        return ''.join(result_parts)

    def call_tool_streaming(self, tool_name: str, arguments: Dict[str, Any]) -> Generator[str, None, None]:
        """Call an MCP tool with streaming support."""
        if not self._initialized:
            raise Exception("MCP client not initialized")

        headers = {
            "NANSEN-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        if self.session_id:
            headers['mcp-session-id'] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                with client.stream("POST", self.server_url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        yield f"Error calling tool: HTTP {response.status_code}"
                        return

                    # Buffer for incomplete lines
                    buffer = ""
                    final_result = None

                    for chunk in response.iter_text():
                        buffer += chunk

                        # Process complete lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()

                            if not line:
                                continue

                            # Parse SSE line
                            parsed = self._parse_sse_line(line)
                            if parsed:
                                # Check for errors
                                if 'error' in parsed:
                                    yield f"Tool error: {parsed['error'].get('message', 'Unknown error')}"
                                    return

                                # Store final result
                                if 'result' in parsed:
                                    final_result = parsed['result']

                                # Yield progress if available
                                if 'progress' in parsed.get('result', {}):
                                    progress = parsed['result']['progress']
                                    yield f"Progress: {progress}\n"

                    # Process any remaining buffer
                    if buffer.strip():
                        parsed = self._parse_sse_line(buffer.strip())
                        if parsed and 'result' in parsed:
                            final_result = parsed['result']

                    # Yield final result
                    if final_result:
                        content = final_result.get('content', [])
                        if content and len(content) > 0:
                            yield content[0].get('text', str(final_result))
                        else:
                            yield str(final_result)
                    else:
                        yield "No result returned from tool"

        except Exception as e:
            yield f"Error: {str(e)}"

    def get_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function calling format."""
        openai_tools = []
        for tool in self.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool['name'],
                    "description": tool.get('description', ''),
                    "parameters": tool.get('inputSchema', {})
                }
            })
        return openai_tools


def initialize_chat(openai_api_key: str, nansen_mcp_url: str, nansen_api_key: str):
    """
    Initialize the chat with Nansen MCP.

    Args:
        openai_api_key: OpenAI API key
        nansen_mcp_url: Nansen MCP server URL
        nansen_api_key: Nansen API key

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    if "chat_initialized" in st.session_state and st.session_state.chat_initialized:
        return True

    try:
        # Initialize MCP client
        mcp_client = NansenMCPClient(nansen_mcp_url, nansen_api_key)
        mcp_client.initialize()

        # Initialize OpenAI client
        openai_client = OpenAI(api_key=openai_api_key)

        # Store in session state
        st.session_state.mcp_client = mcp_client
        st.session_state.openai_client = openai_client
        st.session_state.chat_messages = []
        st.session_state.chat_initialized = True

        return True

    except Exception as e:
        st.error(f"Failed to initialize chat: {str(e)}")
        return False


def run_chat():
    """Run the chat interface."""
    if not st.session_state.get("chat_initialized", False):
        st.warning("Chat not initialized. Please check your configuration.")
        return

    mcp_client: NansenMCPClient = st.session_state.mcp_client
    openai_client: OpenAI = st.session_state.openai_client

    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about blockchain data..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Prepare messages for OpenAI
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant with access to Nansen blockchain data tools. Use the available tools to answer user questions about blockchain activity, tokens, and smart money movements."}
                    ] + st.session_state.chat_messages

                    # Get OpenAI response with function calling
                    tools = mcp_client.get_tools_for_openai()
                    response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=tools[:128] if len(tools) > 128 else tools,  # OpenAI has a limit
                        tool_choice="auto"
                    )

                    assistant_message = response.choices[0].message

                    # Handle tool calls
                    if assistant_message.tool_calls:
                        # Process each tool call
                        for tool_call in assistant_message.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            st.write(f"🔧 Calling tool: `{tool_name}`")

                            # Create placeholder for streaming output
                            tool_output_placeholder = st.empty()
                            tool_result_parts = []

                            # Call the MCP tool with streaming
                            with st.spinner(f"Fetching data from {tool_name}..."):
                                for chunk in mcp_client.call_tool_streaming(tool_name, tool_args):
                                    tool_result_parts.append(chunk)
                                    # Update placeholder with accumulated result
                                    current_result = ''.join(tool_result_parts)
                                    if current_result.startswith("Progress:"):
                                        # Show progress updates
                                        tool_output_placeholder.info(current_result)
                                    else:
                                        # Show partial results
                                        tool_output_placeholder.text(current_result[:500] + "..." if len(current_result) > 500 else current_result)

                            tool_result = ''.join(tool_result_parts)
                            tool_output_placeholder.empty()  # Clear the placeholder

                            # Add tool response to messages
                            messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [tool_call.model_dump()]
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_result
                            })

                        # Get final response with tool results
                        final_response = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages
                        )

                        final_content = final_response.choices[0].message.content
                        st.markdown(final_content)
                        st.session_state.chat_messages.append({"role": "assistant", "content": final_content})
                    else:
                        # No tool calls, just show response
                        content = assistant_message.content
                        st.markdown(content)
                        st.session_state.chat_messages.append({"role": "assistant", "content": content})

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})