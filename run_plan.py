from gradio_client import Client

client = Client("http://127.0.0.1:7860")

print("=" * 60)
print("STEP 1: Calling /plan endpoint...")
print("=" * 60)

result = client.predict(
    message="Plan a 5-day tokyo trip for 2 under $2500, love food & history",
    api_name="/plan"
)

print("PLAN RESULT:")
print(result)
print("--- END PLAN RESULT ---")

print()
print("=" * 60)
print("STEP 2: Calling /confirm endpoint (Execute Plan button)...")
print("=" * 60)

confirm_result = client.predict(api_name="/confirm")
print("CONFIRM RESULT:")
print(confirm_result)
print("--- END CONFIRM RESULT ---")
