from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_llm(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": question}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print(ask_llm("What is machine learning?"))