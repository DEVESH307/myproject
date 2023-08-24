import os
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import random

# Global flag to control the chatbot behavior
rule_based_triggered = False


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


def conversational_chatbot(request, user_input):
    global rule_based_triggered
    cards_data = load_cards_data()
    parent_data = get_parent_data(cards_data)

    # if rule_based_triggered:
    #     return {'bot_reply': '', 'user_input': user_input}

    bot_replies = [
        "I apologize, but I don't have the information you're looking for.",
        "I'm sorry, I'm unable to understand. Please select from the given options.",
        # Add more bot replies here...
    ]
    
    bot_reply = random.choice(bot_replies)

    if bot_reply == "I'm sorry, I'm unable to understand. Please select from the given options.":
        rule_based_triggered = True
        return {'bot_reply': bot_reply, 'parent_data': parent_data, 'user_input': user_input}


    return {'bot_reply': bot_reply, 'user_input': user_input}


def rule_based_chatbot(request, user_input):
    cards_data = load_cards_data()
    parent_data = get_parent_data(cards_data)
    
    # Check if the user input matches a parent card's user input
    matched_parent_card = next((card for card in parent_data if card['user'].lower() == user_input.lower()), None)

    if matched_parent_card:
        bot_reply = matched_parent_card['chatbot']
        related_options = matched_parent_card['related_options']
        related_cards = get_related_cards(cards_data, matched_parent_card['id'])
        return {'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input}

    related_card = next((card for card in cards_data['Card'] if card['user'].lower() == user_input.lower()), None)

    if related_card:
        bot_reply = related_card['chatbot']
        related_options = related_card['related_options']
        related_cards = get_related_cards(cards_data, related_card['id'])
        return {'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input}
    
    return {'bot_reply': "I'm sorry, I cannot understand that input.", 'user_input': user_input}


# def rule_based_chatbot(request, user_input):
#     cards_data = load_cards_data()
#     parent_data = get_parent_data(cards_data)
    
#     matched_parent_card = next((card for card in parent_data if card['user'].lower() == user_input.lower()), None)

#     if matched_parent_card:
#         bot_reply = matched_parent_card['chatbot']
#         # related_options = matched_parent_card['related_options']
#         related_cards = get_related_cards(cards_data, matched_parent_card['id'])
        
#         # Check if the matched card requires user input
#         if matched_parent_card.get('wait_for_user_input', False):
#             return {'bot_reply': 'enter input', 'related_cards': related_cards, 'user_input': user_input}
        
#         return {'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input}

#     related_card = next((card for card in cards_data['Card'] if card['user'].lower() == user_input.lower()), None)

#     if related_card:
#         bot_reply = related_card['chatbot']
#         # related_options = related_card['related_options']
#         related_cards = get_related_cards(cards_data, related_card['id'])
        
#         if related_card.get('wait_for_user_input', False):
#             return {'bot_reply': 'enter input', 'related_cards': related_cards, 'user_input': user_input}
        
#         return {'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input}
    
#     return {'bot_reply': 'I am sorry, I cannot understand that input.', 'user_input': user_input}
    

def get_bot_reply(request):
    if request.method == 'GET':
        user_input = request.GET.get('user_input', '').strip()

    global rule_based_triggered
    if rule_based_triggered:
        rule_based_response = rule_based_chatbot(request, user_input)
        if rule_based_response['bot_reply'] == "I'm sorry, I cannot understand that input.":
            rule_based_triggered = False
            conversational_response = conversational_chatbot(request, user_input)
            return JsonResponse(conversational_response)
        return JsonResponse(rule_based_response)
    else:
        conversational_response = conversational_chatbot(request, user_input)
        return JsonResponse(conversational_response)

