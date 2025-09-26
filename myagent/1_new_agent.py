import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole, FilePurpose, FunctionTool, FileSearchTool, ToolSet
from dotenv import load_dotenv

# Create an AIProjectClient from an endpoint, copied from your Azure AI Foundry project.
# You need to login to Azure subscription via Azure CLI and set the environment variables
project_endpoint = os.environ["PROJECT_ENDPOINT"]  # Ensure the PROJECT_ENDPOINT environment variable is set

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
)

agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="my-agent"
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

project_client.agents.delete_agent(agent.id)
print("Deleted agent")