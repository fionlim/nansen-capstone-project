import json
from typing import Optional, Dict, Any, List, Generator
import httpx


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

