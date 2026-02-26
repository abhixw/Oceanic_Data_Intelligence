import requests
import json

def test_query():
    url = "http://127.0.0.1:8000/ask"
    payload = {"question": "Show the Pie chart of Embarked ports."}
    
    print(f"Sending query: {payload['question']}")
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("\nResponse Answer:")
        print(data['answer'])
        if data['image']:
            print("\nImage generated successfully (base64 length:", len(data['image']), ")")
        else:
            print("\nNo image generated.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_query()
