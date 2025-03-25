from openai import AsyncOpenAI
import asyncio
import json
from functions.registry import FunctionRegistry

client = AsyncOpenAI()

# Initialize the function registry
registry = FunctionRegistry()

# Get all available functions
functions = registry.get_all_functions()

function_tools = [{
    "type": "function",
    "function": function_def
} for function_def in functions]

tools = [{
    "type": "function",
    "function": {
        "name": "use_function_decision",
        "description": "Decide if a function is needed and which function to use. Analyze if the user's request requires a concrete action (like creating, listing, deleting something) or if it's just a question that can be answered directly.",
        "parameters": {
            "type": "object",
            "properties": {
                "use_function": {
                    "type": "boolean",
                    "description": "If TRUE, it means the user's request requires a concrete action using one of the available functions. If FALSE, it means we can respond directly without executing any function."
                },
                "function_name": {
                    "type": "string",
                    "enum": [f["name"] for f in functions],
                    "description": "ONLY if use_function is TRUE, choose which function best meets the user's needs. Don't worry about function arguments at this point - they will be defined later. Available functions:\n" + "\n".join([f"- {f['name']}: {f['description']}" for f in functions])
                },
                "response": {
                    "type": "string",
                    "description": "The response to the user's request. Only if use_function is FALSE. Insert a ▓ at the start of the response and a ░ at the end of the response to indicate the start and the end of the response. Do not include a whitespace after the ▓ or before the ░."
                },
                "function_arguments": {
                    "type": "string",
                    "description": f"The arguments to pass to the function. Only if use_function is TRUE. Available functions and their parameters: {json.dumps({f['name']: f['parameters'] for f in functions})}"
                }
            },
            "required": ["use_function", "function_name", "response", "function_arguments"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

async def handle_streaming_response(response_stream) -> tuple[str, list]:
    """
    Handle streaming response from OpenAI API
    Returns: (full_response, tool_calls_data)
    """
    full_response = ""
    tool_calls_data = []
    current_tool_call = None
    accumulated_arguments = ""
    response_started = False
    response_ended = False
    
    is_tool_call = False
    print("\nAssistant: ", end="", flush=True)
    async for event in response_stream:
        # print(event)
        delta = event.choices[0].delta
        
        # Handle tool calls
        if delta.tool_calls:
            is_tool_call = True
            for tool_call in delta.tool_calls:
                # New tool call started
                if tool_call.id:
                    current_tool_call = {
                        "id": tool_call.id,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": ""
                        },
                        "type": tool_call.type
                    }
                    tool_calls_data.append(current_tool_call)
                # Append to current tool call's arguments
                elif tool_call.function and tool_call.function.arguments:
                    chunk = tool_call.function.arguments
                    accumulated_arguments += chunk
                    current_tool_call["function"]["arguments"] = accumulated_arguments

                    if "▓" in accumulated_arguments and not response_started:
                        start_marker_pos = accumulated_arguments.find("▓")
                        if start_marker_pos != -1:
                            content_after_start = accumulated_arguments[start_marker_pos + 1:]  # +7 to skip "/start/"
                            print(content_after_start, end="", flush=True)
                            full_response += content_after_start
                        response_started = True
                        continue
                    
                    if "░" in accumulated_arguments and not response_ended:
                        end_marker_pos = chunk.find("░")
                        if end_marker_pos != -1:
                            content_before_end = chunk[:end_marker_pos]
                            print(content_before_end, end="", flush=True)
                            full_response += content_before_end
                        response_ended = True
                        continue

                    if response_started and not response_ended:
                        print(chunk, end="", flush=True)
                        full_response += chunk
        
        # Handle normal content
        elif delta.content is not None:
            full_response += delta.content
            print(delta.content, end="", flush=True)
    
    if full_response:
        print()
    
    return full_response, tool_calls_data

async def main():
    print("Welcome to the ChatGPT terminal!")

    context_window = []

    while True:
        user_input = input("\nUser: ")

        context_window.append({
            "role": "user",
            "content": user_input
        })

        # First, let the model decide whether to use a function
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=context_window,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "use_function_decision"}},  # Force the use of decision tool
            stream=True
        )

        full_response, tool_calls_data = await handle_streaming_response(stream)
        
        # Create the complete message from the accumulated data
        message = {
            "role": "assistant",
            "content": full_response if full_response else tool_calls_data[0]["function"]["arguments"]
        }
        
        if tool_calls_data:
            message["tool_calls"] = tool_calls_data
            
            # Process the tool calls
            tool_call = tool_calls_data[0]  # We only handle one tool call for now
            function_decision = json.loads(tool_call["function"]["arguments"])
            
            context_window.append(message)
            
            # If the model decides to use a function
            if function_decision["use_function"]:

                function_args = json.loads(function_decision["function_arguments"])
                
                print("I will execute the function:", function_decision["function_name"])
                print("With parameters:", json.dumps(function_args, indent=2))
                
                # Get the function to check if it requires confirmation
                function_class = registry.get_function(function_decision["function_name"])
                instance = function_class()
                
                # Only ask for confirmation if the function requires it
                should_proceed = True
                if instance.requires_confirmation:
                    # Ask for user confirmation
                    confirmation = input("\nDo you want to proceed? (y/n): ").lower()
                    should_proceed = confirmation == 'y'
                
                if not should_proceed:
                    # Add the cancellation to the context and get model's response
                    context_window.append({
                        "role": "user",
                        "content": "I don't want to proceed with this operation. Please cancel it."
                    })
                    
                    # Get response from the model about the cancellation
                    cancel_response_stream = await client.chat.completions.create(
                        model="gpt-4o",
                        messages=context_window,
                        stream=True
                    )
                    
                    cancel_response_full, _ = await handle_streaming_response(cancel_response_stream)
                    context_window.append({
                        "role": "assistant",
                        "content": cancel_response_full
                    })
                    continue
                
                # Execute the function using the registry
                result = registry.execute_function(function_decision["function_name"], **function_args)
                
                # Add the tool response to the context
                context_window.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result)
                })

                # Get final response from the model about what was done
                final_response_stream = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=context_window,
                    stream=True
                )

                final_response_full, _ = await handle_streaming_response(final_response_stream)
                context_window.append({
                    "role": "assistant",
                    "content": final_response_full
                })
                continue
            else:
                context_window.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps({"success": True})
                })
        else:
            # If no function was called, just add the response to context
            context_window.append(message)

if __name__ == "__main__":
    asyncio.run(main())
