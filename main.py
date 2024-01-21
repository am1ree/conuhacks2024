import re
import json
import openai
import sys
import time
from colorama import init
init(strip=not sys.stdout.isatty()) # strip colors if stdout is redirected
from termcolor import cprint 
from pyfiglet import figlet_format
import asyncio
import webbrowser
import elevenlabs as elabs
from flask import Flask, render_template_string

app = Flask(__name__, static_url_path='')

cprint(figlet_format('Story Buddy', font='starwars'), attrs=['bold'])

inputstory = input("Describe a story you want to hear today: ")

openai.api_key = ''
elabs.set_api_key("")
def split_pages(story_text):
    # Split the story text into pages using the pattern "Page X:"
    pages = re.split(r'Page \d+:', story_text)[1:]
    if pages == []:
        pages = re.split(r'page \d+:', story_text)[1:]
    
    # Clean up leading/trailing whitespaces and create a list of dictionaries
    pages_json = [{"page_number": i + 1, "content": page.strip()} for i, page in enumerate(pages)]
    
    return pages_json
print("Generating story...")
completion = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": "You are an assistant that generates story and clearly separates them by their page number, write the word Page followed by the page number and : and skip to the newline and write the page content, keep all the stories under 5 pages"
        },
        {
            "role": "user",
            "content": "carefully separating each page by the word page and its number can you generate a story " + inputstory + " in under 5 pages",
        },
    ],
)
#print(completion.choices[0].message.content)
pages_json = split_pages(completion.choices[0].message.content)

# Convert the list of dictionaries to JSON

# Print or save the JSON as needed
#print(json_result)
for i in range(len(pages_json)):
    print("generating image " + str(i+1) + "/" +str(len(pages_json)))
    if i == 4:
        time.sleep(10)
    imgprompt = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "create a really short prompt that describes an image representing this part of a story : " + pages_json[i]["content"]
            },
        ],
    )
    pages_json[i]["url"] = openai.images.generate(
    model="dall-e-2",
    prompt=imgprompt.choices[0].message.content,
    n=1,
    size="1024x1024"
    ).data[0].url
    print("generating audio...")
    audio = elabs.generate(
        text=pages_json[i]["content"],
        model="eleven_multilingual_v2"
    )
    elabs.save(audio, str(i)+".mp3")

json_result = json.dumps(pages_json, indent=2)

pages = pages_json

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Storybook</title>
<style>
body {
text-align: center;
font-family: Arial, sans-serif;
}
img {
max-width: 60%;
max-height: 60%;
}
.content-box {
width: 80%;
margin: 20px auto;
padding: 10px;
border: 1px solid #ccc;
border-radius: 5px;
}
</style>
</head>
<body>
<div>
<img src="{{ page['url'] }}" alt="Page Image">
</div>
<div class="content-box">
<audio controls>
<source src="{{ page['page_number'] ~ '.mp3' }}" type="audio/mp3">
Your browser does not support the audio element.
</audio>
<p>{{ page['content'] }}</p>
</div>
<div>
{% if page['page_number'] > 1 %}
<a href="/{{ page['page_number'] - 1 }}">Previous</a>
{% endif %}
{% if page['page_number'] < pages|length %}
<a href="/{{ page['page_number'] + 1 }}">Next</a>
{% endif %}
</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template, page=pages[0], pages=pages)

@app.route('/<int:page_number>')
def show_page(page_number):
    if 1 <= page_number <= len(pages):
        return render_template_string(html_template, page=pages[page_number - 1], pages=pages)
    else:
        return "Page not found."

if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False)