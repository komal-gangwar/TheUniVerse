import google.generativeai as genai

genai.configure(api_key="AIzaSyBvjzdJPP2u3tA4ABMT0kEdXhPpggLKkSg")

for m in genai.list_models():
    print(m.name)
