import os
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import random


# Create your views here.
def chatbot_view(request):
    return render(request, 'chatbot/index.html')

# Function to load cards data from cards.json
def load_cards_data():
    cards_json_path = os.path.join(os.path.dirname(__file__), 'static/chatbot/json/cards.json')
    with open(cards_json_path, 'r') as f:
        cards_data = json.load(f)
    return cards_data


def get_parent_data(cards_data):
    parent_data = [card for card in cards_data['Card'] if card.get('isParent') is True]
    return parent_data


def get_related_cards(cards_data, option):
    related_options = []
    related_entries = []
    for card in cards_data['Card']:
        if card['id'] == option:
            related_options = card['related_options']
            break

    for card in cards_data['Card']:
        if card['id'] in related_options:
            related_entries.append(card)

    return related_entries

def get_bot_reply(request):
    if request.method == 'GET':
        user_input = request.GET.get('user_input', '').strip()
    
    bot_replies = [
        "I apologize, but I don't have the information you're looking for.",
        "I'm sorry, I'm unable to understand. Please select from the given options.",
        # Add more bot replies here...
    ]

    bot_reply = random.choice(bot_replies)

    cards_data = load_cards_data()
    card_contents = [card['user'] for card in cards_data['Card']]

    if bot_reply == "I'm sorry, I'm unable to understand. Please select from the given options.":
        parent_data = get_parent_data(cards_data)
        return JsonResponse({'bot_reply': bot_reply, 'parent_data': parent_data, 'user_input': user_input})
    elif user_input in card_contents:
        card_option = None
        for card in cards_data['Card']:
            if user_input == card['user']:
                card_option = card['id']
                break

        if card_option is not None:
            related_cards = get_related_cards(cards_data, card_option)
            return JsonResponse({'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input})
    else:
        return JsonResponse({'bot_reply': bot_reply, 'user_input': user_input})

def get_bot_reply(request):
    if request.method == 'GET':
        user_input = request.GET.get('user_input', '').strip()

    cards_data = load_cards_data()
    parent_data = get_parent_data(cards_data)
    
    # Check if the user input matches a parent card's user input
    matched_parent_card = next((card for card in parent_data if card['user'].lower() == user_input.lower()), None)

    if matched_parent_card:
        bot_reply = matched_parent_card['chatbot']
        related_options = matched_parent_card['related_options']
        related_cards = get_related_cards(cards_data, matched_parent_card['id'])
        return JsonResponse({'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input})

    # Check if the user input matches a related card's user input
    related_card = next((card for card in cards_data['Card'] if card['user'].lower() == user_input.lower()), None)

    if related_card:
        bot_reply = related_card['chatbot']
        related_options = related_card['related_options']
        related_cards = get_related_cards(cards_data, related_card['id'])
        return JsonResponse({'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input})

    bot_replies = [
        "I apologize, but I don't have the information you're looking for.",
        "I'm sorry, I'm unable to understand. Please select from the given options.",
        # Add more bot replies here...
    ]
    
    bot_reply = random.choice(bot_replies)
    return JsonResponse({'bot_reply': bot_reply, 'parent_data': parent_data, 'user_input': user_input})

def get_bot_reply(request):
    if request.method == 'GET':
        user_input = request.GET.get('user_input', '').strip()

    cards_data = load_cards_data()
    parent_data = get_parent_data(cards_data)
    
    # Check if the user input matches a parent card's user input
    matched_parent_card = next((card for card in parent_data if card['user'].lower() == user_input.lower()), None)

    if matched_parent_card:
        bot_reply = matched_parent_card['chatbot']
        related_options = matched_parent_card['related_options']
        related_cards = get_related_cards(cards_data, matched_parent_card['id'])
        return JsonResponse({'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input})

    related_card = next((card for card in cards_data['Card'] if card['user'].lower() == user_input.lower()), None)

    if related_card:
        bot_reply = related_card['chatbot']
        related_options = related_card['related_options']
        related_cards = get_related_cards(cards_data, related_card['id'])
        return JsonResponse({'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input})
        
    bot_replies = [
        "I apologize, but I don't have the information you're looking for.",
        "I'm sorry, I'm unable to understand. Please select from the given options.",
        # Add more bot replies here...
    ]
    
    bot_reply = random.choice(bot_replies)
    
    if bot_reply == "I'm sorry, I'm unable to understand. Please select from the given options.":
        return JsonResponse({'bot_reply': bot_reply, 'parent_data': parent_data, 'user_input': user_input})
    else:
        return JsonResponse({'bot_reply': bot_reply, 'user_input': user_input})
