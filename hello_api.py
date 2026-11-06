from dotenv import load_dotenv
import anthropic

load_dotenv()                      # reads the key from .env
client = anthropic.Anthropic()     # picks up ANTHROPIC_API_KEY automatically

msg = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello in Kannada and English."}],
)

print(msg.content[0].text)
print(msg.usage)                   # tokens used
print(msg.model)                   # confirms the model