from dataclasses import dataclass
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
from matplotlib.colors import cnames as colors
from utils import get_alternate_phrasing, get_image, get_random_fact, prompt

client = OpenAI()
waffle_file = open("waffles.json", "r")
waffle_data = json.load(waffle_file)
user_name = getenv("USER_NAME", "Random Person")


class CardGrid(ui.grid):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.classes(
            'w-full gap-x-4 gap-y-4 pt-100 px-4 grid-cols-3 max-[1000px]:grid-cols-2 max-[650px]:grid-cols-1')


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
                ui.button('Back', on_click=stepper.previous)
                ui.button('Next', on_click=stepper.next)
        with ui.step(name='History', icon='book'):
            with ui.timeline(side='right'):
                ui.timeline_entry('Initial commit',
                                  title='Project start', subtitle='Some date')
                ui.timeline_entry(
                    'First release', title='Release 0.1', subtitle='Some date')
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


def card(title, description, color, id):
    components = {
        "card": ui.card().style('color: red background-color: red').style(f'background: radial-gradient(circle, {colors[color]} 0%, #014a88 100%)'),
        "image": None,
        "recipe": None,
    }
    with components["card"]:
        components["image"] = ui.image(get_image(name=title, description=description)).style(
            'border-radius: 10px; shadow: 5px 0px 10px #000000')
        components["recipe"] = create_recipe_stepper()
        with ui.card_section().classes('flex'):
            ui.chip("View", icon="ads_click", on_click=lambda waffle=id,
                    components=components: view_component(id, components, "recipe"), color="blue")
            ui.chip("Recipe", icon="book", on_click=lambda waffle=id, components=components: view_component(
                id, components, "recipe"), color="g")
            ui.chip("Fight", icon="connect_without_contact", color="orange")
            ui.chip("Breed", icon="favorite", color="green")
            # Additional actions can be added here
            ui.space()
            ui.separator()
            ui.label(description)


with ui.row().classes('w-full'):
    chat = ui.chat_message(f'Hello {user_name}! Welcome to your waffle-deck. Here you will produce, breed and and stage\n waffles against eachother to produce the ultimate waffle!',
                           name='Waffle Assistant', stamp='Some time ago', avatar='https://robohash.org/waffle')
    ui.timer(1, lambda: get_random_fact(chat, {'user_name': user_name}))
waffle = waffle_data["waffles"][0]
components = {
    "card": ui.card().style('color: red background-color: red').style(f'background: radial-gradient(circle, {colors[waffle["color"]]} 0%, #014a88 100%)'),
    "image": None,
    "recipe": None,
}
with components["card"]:
    # image with rounded corners
    components["image"] = ui.image(get_image(
        name=waffle["name"], description=waffle["description"]
    )).style(
        'border-radius: 10px; shadow: 5px 0px 10px #000000')
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
        ui.label(waffle["description"]).style('color: white')


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
            components["image"] = ui.image(get_image(
                name=waffle["name"], description=waffle["description"]
            ))
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


def progress_stepper_if_all_ingredients_are_available(ingredients: dict, stepper: Stepper):
    if all(ingredients.values()):
        stepper.next()


@ui.refreshable
def ingredients(stepper: Stepper, ingredients: dict):
    for ingredient, available in ingredients.items():
        ui.checkbox(text=ingredient, value=available, on_change=lambda: stepper.next(
        ) if all(ingredients.values()) else None)


@dataclass
class TodoItem:
    name: str
    done: bool = False


@ui.page('/load_card/{color}/{id}')
def load_card(color, id):
    # in the center
    with ui.row().classes('w-full h-full').classes('flex flex-col items-center justify-center'):
        with ui.card().style(f'min-width: 38em; background: radial-gradient(circle, {colors[color]} 0%, #014a88 100%)'):
            # black almost transparent background
            with ui.stepper().props('vertical').style('background: rgba(0, 0, 0, 0.2)').classes('w-full') as stepper:
                with ui.step('New Waffle!'):
                    ui.label(get_alternate_phrasing(f'Fresh {color} waffle card detected! Would you like to start preparing it?')).style(
                        'color: white')
                    with ui.row().classes('w-full h-full').classes('flex flex-col items-center justify-center'):
                        ui.button(get_alternate_phrasing('Start waffle preparation'),
                                  on_click=lambda: stepper.next()).classes('font-bold')
                with ui.step('Plan ingredients'):
                    ui.spinner('audio', size='lg', color=color)

                    ingredients = ['Flour', 'Sugar', 'Eggs', 'Milk']
                    attempts = 3

                    def attempt(attempts) -> list[str]:
                        try:
                            return json.loads(prompt('Come up with a whimsical list of ingredients for a fantasy waffle 4 ingredients respond in json like so {ingredients:[ "ingredient1", "ingedient2" ]}'))['ingredients']
                        except:
                            print(
                                f'failed to parse ingredients trying for {attempts} more times')
                            if attempts > 0:
                                attempts -= 1
                                return attempt(attempts)
                            else:
                                return ['Flour', 'Sugar', 'Eggs', 'Milk']
                    ingredients = attempt(attempts)
                    print(f'got ingredients {ingredients}')
                    checkboxes = []

                    def on_checkbox_change():
                        if all(checkbox.value for checkbox in checkboxes):
                            stepper.next()

                    with ui.column():
                        for ingredient in ingredients[:random.randint(2, len(ingredients))]:
                            checkbox = ui.checkbox(
                                ingredient).on_value_change(on_checkbox_change).style('color: white')
                            checkboxes.append(checkbox)
                        extra_ingredient = {'done': False, 'name': ''}
                        with ui.row().classes('items-center'):
                            ui.checkbox(value=False).bind_value(
                                extra_ingredient, 'done').style('color: white')
                            ui.input(value=extra_ingredient['name']).classes(
                                'flex-grow').bind_value(extra_ingredient, 'name').style('color: white')
                with ui.step('Plan qualities'):
                    ui.spinner('audio', size='lg', color=color)

    # ui.label(f'Loading card {id} with color {color}')
    # ui.spinner('audio', size='lg', color='green')
    # card('Person', 'Description', color, id)


ssl_certfile = getenv('SSL_CERTFILE', None)
ssl_keyfile = getenv('SSL_KEYFILE', None)
if __name__ in {"__main__", "__mp_main__"}:
    print('Starting server')
    if ssl_certfile and ssl_keyfile:
        print('Starting server with SSL')
        ui.run(host='0.0.0.0', port=443,
               ssl_certfile=ssl_certfile, ssl_keyfile=ssl_keyfile,  favicon="favicon.png", title="Waffle Deck")
    else:
        ui.run(host='0.0.0.0', port=80,
               favicon="favicon.png", title="Waffle Deck")
