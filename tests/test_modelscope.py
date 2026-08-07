import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LOCAL_VLM_BASE_URL"),
    api_key=os.getenv("MODELSCOPE_API_KEY"),
)

response = client.chat.completions.create(
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in one sentence.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://modelscope.oss-cn-beijing.aliyuncs.com/demo/images/audrey_hepburn.jpg"
                    },
                },
            ],
        }
    ],
    max_tokens=200,
)

print(response.choices[0].message.content)