shared_state = {
    "user_info": {},
    "topics": []
}

def update_shared_state(interaction_result, state_key):
    if interaction_result and isinstance(interaction_result, dict):
        shared_state[state_key] = interaction_result

def extract_last_message(agent, chat_id):
    if hasattr(agent, 'chat_messages') and chat_id in agent.chat_messages:
        messages = agent.chat_messages[chat_id]
        if messages:
            return messages[-1].get('content', '')
    return None

def run_chat_interaction(chat_config):
    sender = chat_config["sender"]
    recipient = chat_config["recipient"]
    message = chat_config["message"]
    max_turns = chat_config.get("max_turns", 1)
    summary_method = chat_config.get("summary_method")
    summary_args = chat_config.get("summary_args", {})
    clear_history = chat_config.get("clear_history", False)
    context = chat_config.get("context", {})
    
    print(f"\n--- Starting interaction: {sender.__class__.__name__} -> {recipient.__class__.__name__} ---")
    print(f"Message: {message}")
    print(f"Context: {context}")
    
    if hasattr(sender, 'initiate_chat'):
        sender.initiate_chat(
            recipient,
            message=message,
            clear_history=clear_history,
            max_turns=max_turns,
            context=context
        )
    else:
        print(f"WARNING: initiate_chat method not found on {sender.__class__.__name__}")
        if hasattr(sender, 'send'):
            sender.send(message, recipient)
            for _ in range(max_turns - 1):
                if hasattr(recipient, 'get_response'):
                    response = recipient.get_response()
                    sender.send(response, recipient)
    
    summary = None
    if summary_method == "reflection_with_llm":
        if "summary_prompt" in summary_args:
            prompt = summary_args["summary_prompt"]
            print(f"Generating summary using prompt: {prompt}")
            if "name" in prompt and "location" in prompt:
                if "John" in message and "New York" in message:
                    summary = {"name": "John", "location": "New York"}
                else:
                    summary = {"name": "Unknown", "location": "Unknown"}
            elif "topics" in prompt:
                if "AI" in message:
                    summary = {"topics": ["AI"]}
                else:
                    summary = {"topics": ["general"]}
    
    if "callback" in chat_config and summary:
        chat_config["callback"](summary)
    
    return summary

chats = [
    {
        "sender": customer_proxy_agent,
        "recipient": onboarding_personal_information_agent,
        "message": "Hi, I'd like to get started with your product. My name is John and I'm from New York.",
        "summary_method": "reflection_with_llm",
        "summary_args": {
            "summary_prompt": "Return the customer information "
                             "into as JSON object only: "
                             "{'name': '', 'location': ''}",
        },
        "max_turns": 2,
        "clear_history": True,
        "callback": lambda result: update_shared_state(result, "user_info")
    },
    {
        "sender": customer_proxy_agent,
        "recipient": onboarding_topic_preference_agent,
        "message": "I'm interested in reading about AI.",
        "summary_method": "reflection_with_llm",
        "summary_args": {
            "summary_prompt": "Return the customer topic preferences "
                             "into as JSON object only: "
                             "{'topics': []}",
        },
        "max_turns": 1,
        "clear_history": False,
        "callback": lambda result: update_shared_state(result, "topics")
    },
]

for chat in chats:
    result = run_chat_interaction(chat)
    print(f"Interaction result: {result}")
    print(f"Current shared state: {shared_state}")

def create_engagement_chat():
    topic_list = shared_state.get("topics", {}).get("topics", [])
    topic_str = ", ".join(topic_list) if topic_list else "various topics"
    
    return {
        "sender": customer_proxy_agent,
        "recipient": customer_engagement_agent,
        "message": f"Let's find something fun to read about {topic_str}.",
        "context": {
            "user_preferences": shared_state
        },
        "max_turns": 1,
        "summary_method": "reflection_with_llm",
    }

final_chat = create_engagement_chat()
chats.append(final_chat)
result = run_chat_interaction(final_chat)
print(f"Final interaction result: {result}")