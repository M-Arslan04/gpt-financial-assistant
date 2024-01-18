import os
import json
import requests
from openai import OpenAI
import time
from dotenv import load_dotenv, find_dotenv


class FAService:
    client: OpenAI = None
    available_functions = {}

    def __init__(self):
        _: bool = load_dotenv(find_dotenv())  # read local .env file
        self.client: OpenAI = OpenAI()

    @classmethod
    def call_function(self, function_name, ticker, period="annual", limit="1"):
        url = f"https://financialmodelingprep.com/api/v3/{function_name}/{ticker}?period={period}&limit={limit}&apikey={os.environ['FMP_API_KEY']}"
        response = requests.get(url)
        return json.dumps(response.json())

    # Map available functions
    def initialize_dict(self):
        self.available_functions = {
            "get_income_statement": lambda **kwargs: self.call_function(
                "income-statement", **kwargs
            ),
            "get_balance_sheet": lambda **kwargs: self.call_function(
                "balance-sheet-statement", **kwargs
            ),
            "get_cash_flow_statement": lambda **kwargs: self.call_function(
                "cash-flow-statement", **kwargs
            ),
            "get_key_metrics": lambda **kwargs: self.call_function(
                "key-metrics", **kwargs
            ),
            "get_financial_ratios": lambda **kwargs: self.call_function(
                "ratios", **kwargs
            ),
            "get_financial_growth": lambda **kwargs: self.call_function(
                "financial-growth", **kwargs
            ),
        }

    # Creating the Assistant
    # as it is already created, so no need to do it again,
    # we will just use the assistant_id
    def run_assistant(self, user_message):
        if not self.available_functions:
            self.initialize_dict()
        assistant_id = os.environ["ASSISTANT_ID"]

        # Creating a new thread
        thread = self.client.beta.threads.create()
        print("Thread created")

        self.client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_message
        )
        print("Message created")

        # Running the assistant on the created thread
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant_id
        )
        print("Run created")

        # Loop until the run completes or requires action
        while True:
            print("In WHile")
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )

            # Add run steps retrieval here
            run_steps = self.client.beta.threads.runs.steps.list(
                thread_id=thread.id, run_id=run.id
            )
            # print("Run Steps:", run_steps)
            print(f"Run Status: {run.status}")

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    print(f"function_name: {function_name}")

                    function_args = json.loads(tool_call.function.arguments)
                    print(f"function_args: {function_args}")

                    if function_name in self.available_functions:
                        function_to_call = self.available_functions.get(function_name)
                        print(f"function_to_call: {function_to_call}")
                        output = function_to_call(**function_args)

                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "output": output,
                            }
                        )
                # Submit tool outputs and update the run
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                )
            elif run.status == "completed":
                # List the messages to get the response
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                for message in messages.data:
                    role_label = "User" if message.role == "user" else "Assistant"
                    message_content = message.content[0].text.value
                    print(f"{role_label}: {message_content}\n")
                    return message_content
                break
            elif run.status == "failed":
                print("Run failed.")
                break
            elif run.status in ["in_progress", "queued"]:
                print(f"Run is {run.status}. Waiting...")
                time.sleep(5)  # Wait for 5 seconds before checking again
            else:
                print(f"Unexpected status: {run.status}")
                break
