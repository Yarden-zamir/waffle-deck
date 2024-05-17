from requests import get
from datetime import datetime
import asyncio
import random
from nicegui.elements.card import Card
from nicegui.elements.image import Image
from nicegui.elements.stepper import Stepper
from nicegui.elements.chat_message import ChatMessage
import json
from os import getenv, path
from nicegui import app, ui
from openai import OpenAI
client = OpenAI()
waffle_file = open("waffle.json", "r")
waffle_data = json.load(waffle_file)
# response = client.images.generate(
#   model="dall-e-3",
#   prompt="a white siamese cat",
#   size="1024x1024",
#   quality="standard",
#   n=1,
# )
# print(response.data)
# print(response.data[0].url)
# image_url = response.data[0].url
user_name = getenv("WAFFLE_USER", "Naomi")


class card_grid(ui.grid):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.classes('''
            w-full gap-x-4 gap-y-4 pt-12 px-4
            grid-cols-3
            max-[1000px]:grid-cols-2
            max-[650px]:grid-cols-1
        ''')


def get_random_waffle_fact(chat: ChatMessage):
    # every 10 minutes, get a new waffle fact

    if datetime.now().second % (60 * 40) == 0:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a helpful waffle deck assistant, helper to the legandery {user_name}. You will give her Useful facts about waffles that are completely fictional. Funny, crazy, unique, clever, no real facts allowed. DO NOT acknowledge her questions, just give the facts, so no 'sure thing!' etc"},
                {"role": "user", "content": "Give me a waffle fact"},
            ],
            temperature=1,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        # chat.clear()
        if len(chat.default_slot.children) > 1 and random.random() < 0.45:
            [waffle_fact.delete()
             for waffle_fact in chat.default_slot.children[1:]]
        if random.random() < 0.5:
            with chat:
                return ui.label(response.choices[0].message.content)


def get_waffle_image(waffle):
    # check if image file exists
    if path.exists(f"cache/{waffle['name']}.png"):
        return f"cache/{waffle['name']}.png"
    print("No image found for waffle", waffle["name"], "generating...")
    image_url = client.images.generate(
        model="dall-e-3",
        prompt=f"{waffle['description']}      generate an image of this waffle in the style of adventure time art",
        size="1024x1024",
        quality="standard",
        n=1,
    ).data[0].url
    # write image to cache
    # with w
    image = image_url
    with get(image_url, stream=True) as r:
        with open(f"cache/{waffle['name']}.png", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    waffle["image"] = f"cache/{waffle['name']}.png"
    # write the updated waffle data to the file
    with open("waffle.json", "w") as f:
        json.dump(waffle_data, f, indent=4)
    return image


def recipe():
    with ui.stepper().props('vertical').classes('w-full') as stepper:
        with ui.step(name='Batter Ingredients'):
            with ui.list().props('dense separator'):
                ui.item('1/2 cup Rainbow flour')
                ui.item('2 Goose eggs')
                ui.item('1 small Goose neck, defeathered')
                ui.item('1/2 cup fluffed purple sugar')
                ui.item('1/2 cup Yak milk')
            with ui.stepper_navigation():
                ui.button('Next', on_click=stepper.next)
        with ui.step(name='Qualities', icon='star'):
            with ui.stepper_navigation():
                ui.button('Back', on_click=stepper.previous)
            columns = [
                {'name': 'quality', 'label': 'Quality',
                    'field': 'quality', 'required': True, 'align': 'left'},
                {'name': 'rating', 'label': 'Rating',
                    'field': 'rating', 'sortable': True},
            ]
            rows = [
                {'quality': 'Crispiness', 'rating': 4},
                {'quality': 'Fluffiness', 'rating': 6},
                {'quality': 'Sweetness', 'rating': 5},
                {'quality': 'Texture', 'rating': 5},
            ]
            ui.table(columns=columns, rows=rows, row_key='name')
            with ui.stepper_navigation():
                ui.button('Next', on_click=stepper.next)
        with ui.step(name='History', icon='book'):
            with ui.stepper_navigation():
                ui.button('Back', on_click=stepper.previous)
            with ui.timeline(side='right'):
                ui.timeline_entry('Rodja and Falko start working on NiceGUI.',
                                title='Initial commit',
                                subtitle='May 07, 2021')
                ui.timeline_entry('The first PyPI package is released.',
                                title='Release of 0.1',
                                subtitle='May 14, 2021')
                ui.timeline_entry('Large parts are rewritten to remove JustPy '
                                'and to upgrade to Vue 3 and Quasar 2.',
                                title='Release of 1.0',
                                subtitle='December 15, 2022',
                                icon='rocket')

        stepper.classes('h-full minimal-padding')
        stepper.style('padding-left: 5px')
        stepper.set_visibility(False)
        return stepper


def view_waffle(waffle, card: Card, image: Image, recipe: Stepper):
    # hides the image and replaces it with a table of stats
    image.set_visibility(False)
    recipe.set_visibility(True)


with ui.header(elevated=True):
    ui.label("Naomi's Waffle Deck")

with ui.row().classes('w-full'):
    chat = ui.chat_message(f'Hello {user_name}, Welcome to your waffle-deck. Here you will produce, breed and and stage\n waffles against eachother to produce the ultimate waffle!',
                           name='Waffle M.A.K.Er 4861',
                           stamp='Some time ago probably',
                           avatar='https://robohash.org/waffle%20maker')

    ui.timer(1, lambda: get_random_waffle_fact(chat))


def update_progress_bar(progress_bar):
    now = datetime.now()
    minutes_since_hour = now.minute + now.second / 60
    progress = minutes_since_hour / 53

    # round progress to whole number and max at 1.0
    progress_bar.value = round(progress, 2) if progress < 1.0 else 1.0


def reset_progress_bar(progress_bar):
    progress_bar.value = 0


progress_bar = ui.linear_progress(value=0, color="striped")

# Update the progress bar every second
ui.timer(1, lambda: update_progress_bar(progress_bar))

# Reset the progress bar when clicked
progress_bar.on('click', lambda: reset_progress_bar(progress_bar))
card_dict = {}
with card_grid().classes('w-full'):
    for waffle in waffle_data["waffles"]:

        # each card takes half the screen
        card_dict[waffle["name"]] = ui.card().tight().classes('w-full h-full')
        with card_dict[waffle["name"]]:
            # Replace get_waffle_image(waffle) with waffle["name"] for simplicity
            card_dict[waffle["name"] +
                      "_image"] = ui.image(get_waffle_image(waffle))
            card_dict[waffle["name"] +
                      "_recipe"] = recipe()
            with ui.card_section().classes('flex'):
                ui.chip("View", icon="ads_click", on_click=lambda waffle=waffle: view_waffle(
                    waffle, card=card_dict[waffle["name"]], image=card_dict[waffle["name"]+"_image"], recipe=card_dict[waffle["name"]+"_recipe"]), color="blue")
                ui.chip("Fight", icon="connect_without_contact", color="orange")
                ui.chip("Breed", icon="favorite", color="green")
                # ui.button(icon='touch_app').props('outline round').classes('shadow-lg')
                # ui.button(icon='touch_app', on_click=lambda :print("hi")).props('outline round').classes('shadow-lg')
                ui.space()
                ui.separator()
                ui.label(waffle["description"])
dt = datetime.now()


def handle_connection():
    # device =
    global dt
    dt = datetime.now()


app.on_connect(handle_connection)

label = ui.label()
ui.timer(1, lambda: label.set_text(f'Last new connection: {dt:%H:%M:%S}'))

# check if device is mobile
print(ui.context.client.content.__sizeof__())
# ui.run()
ui.run()
