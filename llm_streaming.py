from google import genai
client = genai.Client()

def llm_streaming(input) -> list[str]:
    stream = client.interactions.create(
        model="gemini-3.8-flash",
        input="Explain how AI works",
        stream=True
    )

    for event in stream:
        print(event)

llm_streaming("Explain how AI works")
