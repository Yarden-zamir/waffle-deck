from requests import get
from datetime import datetime
import random
import json
from os import getenv, path
from nicegui import app, ui
from openai import OpenAI
from nicegui.elements.card import Card
from nicegui.elements.image import Image
from nicegui.elements.stepper import Stepper
from nicegui.elements.chat_message import ChatMessage

client = OpenAI()
waffle_file = open("waffles.json", "r")
waffle_data = json.load(waffle_file)
user_name = getenv("USER_NAME","Random Person")

class CardGrid(ui.grid):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.classes('w-full gap-x-4 gap-y-4 pt-12 px-4 grid-cols-3 max-[1000px]:grid-cols-2 max-[650px]:grid-cols-1')

def get_random_fact(chat: ChatMessage):
    if datetime.now().second % (60 * 40) == 0:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a helpful assistant to {user_name}. You will give fictional, funny, and unique facts about waffles. DO NOT acknowledge questions."},
                {"role": "user", "content": "Give me a waffle fact"},
            ],
            temperature=1,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        if len(chat.default_slot.children) > 1 and random.random() < 0.45:
            for fact in chat.default_slot.children[1:]:
                fact.delete()
        if random.random() < 0.5:
            with chat:
                return ui.label(response.choices[0].message.content)

def get_image(waffle):
    if path.exists(f"cache/{waffle['name']}.png"):
        return f"cache/{waffle['name']}.png"
    print(f"No image found for {waffle['name']}, generating...")
    image_url = client.images.generate(
        model="dall-e-3",
        prompt=f"{waffle['description']} in the style of adventure time art",
        size="1024x1024",
        quality="standard",
        n=1,
    ).data[0].url

    with get(image_url, stream=True) as r:
        with open(f"cache/{waffle['name']}.png", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    waffle["image"] = f"cache/{waffle['name']}.png"
    with open("waffles.json", "w") as f:
        json.dump(waffle_data, f, indent=4)
    return waffle["image"]

def create_recipe_stepper():
    with ui.stepper().props('vertical').classes('w-full') as stepper:
        with ui.step(name='Ingredients'):
            with ui.list().props('dense separator'):
                ui.item('1/2 cup flour')
                ui.item('2 eggs')
                ui.item('1/2 cup sugar')
                ui.item('1/2 cup milk')
            with ui.stepper_navigation():
                ui.button('Next', on_click=stepper.next)
        with ui.step(name='Qualities', icon='star'):
            columns = [
                {'name': 'quality', 'label': 'Quality', 'field': 'quality', 'required': True, 'align': 'left'},
                {'name': 'rating', 'label': 'Rating', 'field': 'rating', 'sortable': True},
            ]
            rows = [
                {'quality': 'Crispiness', 'rating': 4},
                {'quality': 'Fluffiness', 'rating': 6},
                {'quality': 'Sweetness', 'rating': 5},
                {'quality': 'Texture', 'rating': 5},
            ]
            ui.table(columns=columns, rows=rows, row_key='name')
            with ui.stepper_navigation():
                ui.button('Back', on_click=stepper.previous)
                ui.button('Next', on_click=stepper.next)
        with ui.step(name='History', icon='book'):
            with ui.timeline(side='right'):
                ui.timeline_entry('Initial commit', title='Project start', subtitle='Some date')
                ui.timeline_entry('First release', title='Release 0.1', subtitle='Some date')
        stepper.classes('h-full minimal-padding')
        stepper.style('padding-left: 5px')
        stepper.set_visibility(False)
        return stepper


def view_component(waffle, components, component_key):
    print(components["recipe"].visible)
    # Hide all components first
    protected_components = ["card"]
    main_component = components["image"]
    for key, component in components.items():
        if key not in protected_components and key != "recipe":
            component.set_visibility(False)
    # Show the specified component
    if components["recipe"].visible:
        print('vis')
        main_component.set_visibility(True)
        components[component_key].set_visibility(False)
    elif component_key in components:
        components["recipe"].set_visibility(True)

with ui.header(elevated=True):
    ui.label(f"{user_name}'s Waffle Deck")

with ui.row().classes('w-full'):
    chat = ui.chat_message(f'Hello {user_name}! Welcome to your waffle-deck. Here you will produce, breed and and stage\n waffles against eachother to produce the ultimate waffle!', name='Waffle Assistant', stamp='Some time ago', avatar='https://robohash.org/waffle')

    ui.timer(1, lambda: get_random_fact(chat))

def update_progress_bar(progress_bar):
    now = datetime.now()
    minutes_since_hour = now.minute + now.second / 60
    progress = minutes_since_hour / 60
    progress_bar.value = round(progress, 2) if progress < 1.0 else 1.0

def reset_progress_bar(progress_bar):
    progress_bar.value = 0

progress_bar = ui.linear_progress(value=0, color="striped")
ui.timer(1, lambda: update_progress_bar(progress_bar))
progress_bar.on('click', lambda: reset_progress_bar(progress_bar))

waffle_dict = {}
with CardGrid().classes('w-full'):
    for waffle in waffle_data["waffles"]:
        components = {
            "card": ui.card().tight().classes('w-full h-full'),
            "image": None,
            "recipe": None,
        }
        waffle_dict[waffle["name"]] = components
        with components["card"]:
            components["image"] = ui.image(get_image(waffle))
            components["recipe"] = create_recipe_stepper()
            with ui.card_section().classes('flex'):
                ui.chip("View", icon="ads_click", on_click=lambda waffle=waffle,
                        components=components: view_component(waffle, components, "recipe"), color="blue")
                ui.chip("Recipe", icon="book", on_click=lambda waffle=waffle, components=components: view_component(
                    waffle, components, "recipe"), color="g")
                ui.chip("Fight", icon="connect_without_contact", color="orange")
                ui.chip("Breed", icon="favorite", color="green")
                # Additional actions can be added here
                ui.space()
                ui.separator()
                ui.label(waffle["description"])

ssl_certfile = getenv('SSL_CERTFILE', None)
ssl_keyfile = getenv('SSL_KEYFILE', None)
if __name__ in {"__main__", "__mp_main__"}:
    print('Starting server')
    if ssl_certfile and ssl_keyfile:
        print('Starting server with SSL')
        ui.run(host='0.0.0.0', port=443,,
               ssl_certfile=ssl_certfile, ssl_keyfile=ssl_keyfile)
    else:
        ui.run(host='0.0.0.0', port=80)
