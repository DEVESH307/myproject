import os
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
import random

# Global flag to control the chatbot behavior
rule_based_triggered = False

# Global dictionaries
payment_status_info = {
    "Company ID": None,
    "Transaction ID": None
}

payment_history_info = {
    "Company ID": None,
    "Date Range": {
        "Start Date": None,
        "End Date": None
    },
    "Time Period": None
}

# Create your views here.
def chatbot_view(request):
    return render(request, 'chatbot/index.html')


# Function to load cards data from cards.json
def load_cards_data():
    cards_json_path = os.path.join(os.path.dirname(__file__), 'static/chatbot/json/cards.json')
    with open(cards_json_path, 'r') as f:
        cards_data = json.load(f)
    return cards_data


def find_current_card_id(data, user_input):
    for conversation in data["Card"]:
        if user_input.lower() == conversation["user"].lower() or user_input == str(conversation["id"]):
            return conversation["id"]
    return None


def get_related_cards(data, current_card_id):
    # Initialize an empty list to store related option cards
    related_options = []
    
    # Find the current card based on the provided ID
    current_card = next((card for card in data["Card"] if card["id"] == current_card_id), None)
    
    # Check if the current card exists and has related options
    if current_card and "related_options" in current_card:
        # Iterate through each option ID in the related_options list of the current card
        for option_id in current_card["related_options"]:
            # Find the option card based on the option ID
            option_card = next((card for card in data["Card"] if card["id"] == option_id), None)
            if option_card:
                # Append the option card to the list of related options
                related_options.append(option_card)
    
    # Return the list of related option cards
    return related_options


def get_parent_data(data, current_card_id):
    return get_related_cards(data, current_card_id)


def is_valid_company_id(company_id):
    if len(company_id) < 10:
        return False, "Company ID should have at least 10 digits."
    return True, None


def is_valid_transaction_id(transaction_id):

    if len(transaction_id) < 10:
        return False, "Transaction ID should have at least 10 digits."
    return True, None


def paymentStatus(user_input, current_card_id):
    payment_status_info = {"Company ID": None, "Transaction ID": None}
    response_data = {"current_card_id": None, "bot_reply": None, "is_valid_company": None, "is_valid_transaction": None}

    response_data["current_card_id"] = current_card_id
    if current_card_id == 5 and user_input:
        is_valid_company, company_error_message = is_valid_company_id(user_input)
        response_data["is_valid_company"] = is_valid_company
        if is_valid_company:
            payment_status_info["Company ID"] = user_input
        else:
            bot_reply = f"Sorry, you have entered an invalid Company ID. {company_error_message}"
            response_data['bot_reply'] = bot_reply
            response_data['user_input'] = user_input

    elif current_card_id == 6 and user_input:
        is_valid_transaction, transaction_error_message = is_valid_transaction_id(user_input)
        response_data["is_valid_transaction"] = is_valid_transaction
        if is_valid_transaction:
            payment_status_info["Transaction ID"] = user_input
            response_data["current_card_id"] = current_card_id
        else:
            bot_reply = f"Sorry, you have entered an invalid Transaction ID. {transaction_error_message}"
            response_data['bot_reply'] = bot_reply
            response_data['user_input'] = user_input
    return payment_status_info, response_data



def paymentHistory():
    pass


def conversational_chatbot(user_input):
    global rule_based_triggered
    cards_data = load_cards_data()

    current_card_id = 0
    parent_data = get_parent_data(cards_data, current_card_id)

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


def rule_based_chatbot(user_input):
    cards_data = load_cards_data()

    # Find the current card ID
    current_card_id = find_current_card_id(cards_data, user_input)

    current_card = next((card for card in cards_data["Card"] if card["id"] == current_card_id), None)

    if current_card:
        bot_reply = current_card['chatbot']
        related_cards = get_related_cards(cards_data, current_card_id)
        return {'bot_reply': bot_reply, 'related_cards': related_cards, 'user_input': user_input}

    # Handle the case when the current card is not found
    return {'bot_reply': "I'm sorry, I cannot understand that input.", 'user_input': user_input}


class GetBotReplyAPIView(APIView):
    @csrf_exempt
    def get(self, request):
        user_input = request.GET.get('user_input', '').strip()

        global rule_based_triggered
        if rule_based_triggered:
            rule_based_response = rule_based_chatbot(user_input)
            if rule_based_response['bot_reply'] == "I'm sorry, I cannot understand that input.":
                rule_based_triggered = False
                conversational_response = conversational_chatbot(user_input)
                return JsonResponse(conversational_response)
            return JsonResponse(rule_based_response)
        else:
            conversational_response = conversational_chatbot(user_input)
            return JsonResponse(conversational_response)
        
    @csrf_exempt
    def post(self, request):
        user_input = request.POST.get('user_input', '').strip()
        user_input_type = request.POST.get('user_input_type', '').strip()
        cards_data = load_cards_data()
        current_card_id = request.session.get('current_card_id', None)

        # Find the current card ID
        if user_input_type == "clickedCardMessage":
            current_card_id = find_current_card_id(cards_data, user_input)
            request.session['current_card_id'] = current_card_id
            return JsonResponse({'bot_reply': f"Clicked card {current_card_id}.", 'user_input': user_input, 'user_input_type': user_input_type})
        elif user_input_type == "userMessage":
            pass
        else:
            current_card_id = None
            # current_card_id_tracker = None   
        try:
            if current_card_id == 5 or current_card_id == 6:
                print(current_card_id)
                payment_status_info ,payment_status_response = paymentStatus(user_input, current_card_id)
                if payment_status_response.get('is_valid_company') or payment_status_response.get('is_valid_transaction'):
                    return JsonResponse({'bot_reply': "Please allow me a moment; I am in the process of fetching your Payment Status for the past month.", 'payment_status_response': payment_status_response, 'payment_status_info': payment_status_info})
                else:
                    return JsonResponse({'bot_reply': payment_status_response['bot_reply'], 'payment_status_info': payment_status_info})
                
            else:
                raise ValueError("Invalid current_card_id")
        except ValueError as e:
            return JsonResponse({'bot_reply': str(e), 'user_input_type': user_input_type, 'user_input': user_input, 'current_card_id':current_card_id}, status=400)