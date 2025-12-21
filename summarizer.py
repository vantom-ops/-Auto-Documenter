import openai

openai.api_key = "YOUR_API_KEY"

def summarize(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Explain this data:\n{text}"}
        ]
    )
    return response.choices[0].message.content
