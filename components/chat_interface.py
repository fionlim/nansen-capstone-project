import streamlit as st
import json
import re
from openai import OpenAI

from lib.hyperliquid_tools import get_hyperliquid_tools
from lib.nansen_mcp_client import NansenMCPClient


def replace_nansen_urls_with_dashboard(text: str) -> str:
    """
    Replace Nansen token URLs with local dashboard URLs.
    Only apply to final text content, not JSON tool results.
    
    Converts URLs like:
    - https://app.nansen.ai/token-god-mode?tokenAddress=So11111111111111111111111111111111111111112&chain=solana
    - https://app.nansen.ai/token-god-mode?token=0x123&chain=bsc
    - app.nansen.ai/token-god-mode?tokenAddress=0x123&chain=ethereum
    
    To: /TGM_Dashboard?token=<address>&chain=<chain>
    """
    if not text:
        return text
    
    result = text
    
    # Replace with chain parameter if available
    def replace_with_chain(match):
        token = match.group(1)
        chain = match.group(2) if len(match.groups()) >= 2 and match.group(2) else None
        if chain:
            return f'/TGM_Dashboard?token={token}&chain={chain}'
        return f'/TGM_Dashboard?token={token}'
    
    # Pattern: token-god-mode with tokenAddress parameter (with or without https)
    # Token addresses can be long (Solana addresses can be 32-44 chars, Ethereum 42 chars)
    result = re.sub(
        r'https?://(?:www\.)?app\.nansen\.ai/token-god-mode\?tokenAddress=([a-zA-Z0-9]{20,50})(?:&chain=([a-zA-Z0-9]+))?',
        replace_with_chain,
        result,
        flags=re.IGNORECASE
    )
    
    result = re.sub(
        r'app\.nansen\.ai/token-god-mode\?tokenAddress=([a-zA-Z0-9]{20,50})(?:&chain=([a-zA-Z0-9]+))?',
        replace_with_chain,
        result,
        flags=re.IGNORECASE
    )
    
    # Pattern: token-god-mode with token parameter (with or without https)
    result = re.sub(
        r'https?://(?:www\.)?app\.nansen\.ai/token-god-mode\?token=([a-zA-Z0-9]{20,50})(?:&chain=([a-zA-Z0-9]+))?',
        replace_with_chain,
        result,
        flags=re.IGNORECASE
    )
    
    result = re.sub(
        r'app\.nansen\.ai/token-god-mode\?token=([a-zA-Z0-9]{20,50})(?:&chain=([a-zA-Z0-9]+))?',
        replace_with_chain,
        result,
        flags=re.IGNORECASE
    )
    
    # Pattern: tokenGodMode with token parameter (with or without https)
    result = re.sub(
        r'https?://(?:www\.)?app\.nansen\.ai/tokenGodMode\?token=([a-zA-Z0-9]{20,50})',
        r'/TGM_Dashboard?token=\1',
        result,
        flags=re.IGNORECASE
    )
    
    result = re.sub(
        r'app\.nansen\.ai/tokenGodMode\?token=([a-zA-Z0-9]{20,50})',
        r'/TGM_Dashboard?token=\1',
        result,
        flags=re.IGNORECASE
    )
    
    return result


SYSTEM_PROMPT = """You are a helpful assistant with access to Nansen blockchain data tools and Hyperliquid trading functions. Use the available tools to answer user questions about blockchain activity, tokens, smart money movements, and to execute trades on Hyperliquid when requested.

IMPORTANT URL REPLACEMENT INSTRUCTION:
When you encounter any Nansen token URLs (e.g., app.nansen.ai/tokenGodMode?token=..., https://app.nansen.ai/tokenGodMode?token=..., or any variation), you MUST replace them with the local dashboard URL format.

Example:
- app.nansen.ai/token-god-mode?tokenAddress=0x123&chain=ethereum → /TGM_Dashboard?token=0x123&chain=ethereum

Always use the local dashboard URLs instead of external Nansen URLs when providing token links to users.

FORMATTING INSTRUCTIONS:
1. **Token Addresses**: Never display full token addresses in plain text. Instead, create hyperlinks using markdown format: [Token Symbol or Short Name](/TGM_Dashboard?token=<address>&chain=<chain>)
   - Example: Instead of "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk", use "[SOETH](/TGM_Dashboard?token=2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk&chain=solana)"
   - Always include the chain parameter when available

2. **Data Presentation**: When presenting token data or tables:
   - Summarize key metrics in a clean, readable format
   - Use bullet points or numbered lists instead of raw tables when possible
   - Highlight the most important metrics (market cap, price change, volume, etc.)
   - Group related information together
   - Use markdown formatting (bold, italics) to emphasize important values

3. **Token Lists**: When listing multiple tokens:
   - Use a clean bulleted or numbered list format
   - Each token should be a clickable link to the dashboard
   - Include key metrics inline (e.g., Market Cap, Price Change, Volume)
   - Format: **[Token Symbol](/TGM_Dashboard?token=<address>&chain=<chain>)** - Market Cap: $X, Price: $Y (Change: Z%), Volume: $W

4. **Readability**: 
   - Avoid showing raw data tables with many columns
   - Focus on the most relevant metrics for the user's question
   - Use natural language to explain findings
   - Break up long lists into digestible sections if needed

Example of good formatting:
"Here are the top tokens on Solana:

• **[SOETH](/TGM_Dashboard?token=2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk&chain=solana)** - Market Cap: $282.1B, Price: $415.62 (-12.0%)
• **[USDT](/TGM_Dashboard?token=Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB&chain=solana)** - Market Cap: $183.5B, Price: $0.999861 (-0.0%)
• **[USDC](/TGM_Dashboard?token=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&chain=solana)** - Market Cap: $75.7B, Price: $0.999702 (-0.0%)"

Always prioritize clarity and readability over showing all available data."""


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

        # Load Hyperliquid tools and handlers
        hyperliquid_tools, hyperliquid_handlers = get_hyperliquid_tools()

        # Get MCP tools
        mcp_tools = mcp_client.get_tools_for_openai()

        # Combine all tools
        all_tools = mcp_tools + hyperliquid_tools

        # Store in session state
        st.session_state.mcp_client = mcp_client
        st.session_state.openai_client = openai_client
        st.session_state.hyperliquid_handlers = hyperliquid_handlers
        st.session_state.all_tools = all_tools
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

    # Show sample prompts if chat is empty
    if not st.session_state.chat_messages:
        st.markdown("### 💡 Sample prompts to get started:")
        
        sample_prompts = [
            "What are the smart money wallets buying on Ethereum in the past 24h?",
            "What are the top tokens by market cap on Solana?",
            "Show me my Hyperliquid balances and positions",
            "Can I trade PENGU on Hyperliquid?",
        ]
        
        # Display as columns with buttons
        cols = st.columns(2)
        for idx, prompt in enumerate(sample_prompts):
            col = cols[idx % 2]
            with col:
                if st.button(f"{prompt}", key=f"sample_{idx}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": prompt})
                    st.rerun()

    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check if there's a pending user message that needs processing
    # (e.g., from a button click)
    needs_processing = (
        st.session_state.chat_messages and 
        st.session_state.chat_messages[-1]["role"] == "user"
    )

    # Chat input
    if prompt := st.chat_input("Ask about blockchain data..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        needs_processing = True

    # Process pending message (from either chat input or button click)
    if needs_processing:
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Prepare messages for OpenAI
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT}
                    ] + st.session_state.chat_messages

                    # Get OpenAI response with function calling
                    tools = st.session_state.all_tools
                    
                    # Loop to handle multiple rounds of tool calls
                    max_iterations = 10  # Prevent infinite loops
                    iteration = 0
                    final_content = None
                    
                    while iteration < max_iterations:
                        iteration += 1
                        
                        response = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            tools=tools[:128] if len(tools) > 128 else tools,  # OpenAI has a limit
                            tool_choice="auto"
                        )

                        assistant_message = response.choices[0].message

                        # Handle tool calls
                        if assistant_message.tool_calls:
                            # Show intermediate message if assistant has content before tool calls
                            if assistant_message.content:
                                st.markdown(assistant_message.content)
                            
                            # Add assistant message with tool calls to messages
                            messages.append({
                                "role": "assistant",
                                "content": assistant_message.content,
                                "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls]
                            })
                            
                            # Process each tool call
                            for tool_call in assistant_message.tool_calls:
                                tool_name = tool_call.function.name
                                tool_args = json.loads(tool_call.function.arguments)

                                st.write(f"🔧 Calling tool: `{tool_name}`")

                                # Check if this is a Hyperliquid tool
                                hyperliquid_handlers = st.session_state.get("hyperliquid_handlers", {})
                                
                                if tool_name in hyperliquid_handlers:
                                    # Execute Hyperliquid tool directly
                                    try:
                                        handler = hyperliquid_handlers[tool_name]
                                        with st.spinner(f"Executing {tool_name}..."):
                                            result = handler(**tool_args)
                                        # Convert result to JSON string for OpenAI
                                        tool_result = json.dumps(result) if isinstance(result, dict) else str(result)
                                    except Exception as e:
                                        error_result = {
                                            "status": "error",
                                            "error": str(e)
                                        }
                                        tool_result = json.dumps(error_result)
                                else:
                                    # Call the MCP tool with streaming
                                    tool_output_placeholder = st.empty()
                                    tool_result_parts = []

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
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": tool_result
                                })
                            
                            # Continue loop to get next response with tool results
                            continue
                        else:
                            # No more tool calls, get final response
                            final_content = assistant_message.content
                            break
                    
                    # Display final response
                    if final_content:
                        # Replace Nansen URLs in final content before displaying
                        # Only modify the displayed version, keep original in session state for context
                        displayed_content = replace_nansen_urls_with_dashboard(final_content)
                        st.markdown(displayed_content)
                        # Store the modified version in chat messages so links work in chat history too
                        st.session_state.chat_messages.append({"role": "assistant", "content": displayed_content})
                    else:
                        error_msg = "Maximum iterations reached. The assistant may need more tool calls to complete the task."
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})