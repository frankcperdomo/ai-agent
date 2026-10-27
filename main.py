import argparse
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from prompts import system_prompt
from call_function import available_functions, call_function

MAX_ITERATIONS = 20

parser = argparse.ArgumentParser(description="Chatbot")
parser.add_argument("user_prompt", type=str, help="User prompt")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
args = parser.parse_args()

load_dotenv()
api_key = os.environ.get("OPENROUTER_API_KEY")
if api_key is None:
    raise RuntimeError("OPENROUTER_API_KEY not found. Make sure it's set in your .env file.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": args.user_prompt},
]

if args.verbose:
    print(f"User prompt: {args.user_prompt}")

for _ in range(MAX_ITERATIONS):
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=messages,
        tools=available_functions,
        temperature=0,
    )

    if response.usage is None:
        raise RuntimeError("No usage data in response. The API request may have failed.")

    if args.verbose:
        print(f"Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Response tokens: {response.usage.completion_tokens}")

    message = response.choices[0].message
    messages.append(message)

    if not message.tool_calls:
        if not message.content:
            messages.append({"role": "user", "content": "Continue working on the task. Call a function or give your final answer."})
            continue
        print("Final response:")
        print(message.content)
        break

    for tool_call in message.tool_calls:
        result_message = call_function(tool_call, verbose=args.verbose)
        if not result_message.get("content"):
            raise RuntimeError(f"Empty result from function call: {tool_call.function.name}")
        if args.verbose:
            print(f"-> {result_message['content']}")
        messages.append(result_message)
else:
    print(f"Error: Agent did not produce a final response within {MAX_ITERATIONS} iterations.")
    sys.exit(1)