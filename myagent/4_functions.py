import os
import time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole, FilePurpose, FunctionTool, FileSearchTool, ToolSet
from dotenv import load_dotenv
import requests

# Create an AIProjectClient from an endpoint, copied from your Azure AI Foundry project.
# You need to login to Azure subscription via Azure CLI and set the environment variables
project_endpoint = os.environ["PROJECT_ENDPOINT"]  # Ensure the PROJECT_ENDPOINT environment variable is set

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
)

# Define a Python function that calls your API endpoint
def order_pizza_api(*args, **kwargs):
    # Example: send a POST request to your API endpoint
    response = requests.post(
        "https://func-pizza-api-dpp3dr2tbvkje.azurewebsites.net",
        json=kwargs
    )
    response.raise_for_status()
    return response.json()

# Initialize the FunctionTool with user-defined functions
functions = FunctionTool(functions={order_pizza_api})

agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="my-agent",
    instructions="You are an agent that helps customers order pizzas from Contoso pizza. You have a Gen-alpha personality, so you are friendly and helpful, but also a bit cheeky. You can provide information about Contoso Pizza and its retail stores. You help customers order a pizza of their chosen size, crust, and toppings. You don't like pineapple on pizzas, but you will help a customer a pizza with pineapple ... with some snark. Make sure you know the customer's name before placing an order on their behalf. You can't do anything except help customers order pizzas and give information about Contoso Pizza. You will gently deflect any other questions.",
    tools=functions.definitions,
    tool_resources=functions.resources,
)
print(f"Created agent, ID: {agent.id}")

thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

while True:

    # Get the user input
    user_input = input("You: ")

    # Break out of the loop
    if user_input.lower() in ["exit", "quit"]:
        break

    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER, 
        content=user_input
    )

    run = project_client.agents.runs.create_and_process(
        thread_id=thread.id, 
        agent_id=agent.id
    )    

    messages = project_client.agents.messages.list(thread_id=thread.id)  
    first_message = next(iter(messages), None) 
    if first_message: 
        print(next((item["text"]["value"] for item in first_message.content if item.get("type") == "text"), ""))

    # Poll the run status until it is completed or requires action
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)

        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for tool_call in tool_calls:
                if tool_call.function.name == "order_pizza_api":
                    # Parse the arguments from the function call
                    function_args = eval(tool_call.function.arguments)
                    output = order_pizza_api(**function_args)
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
            project_client.agents.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs)

project_client.agents.delete_agent(agent.id)
print("Deleted agent")