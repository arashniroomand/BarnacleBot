import sys
print(f"Python executable: {sys.executable}")

try:
    import openai
    print("OpenAI imported successfully!")
    print(f"OpenAI version: {openai.__version__}")
except ImportError as e:
    print(f"Import error: {e}")