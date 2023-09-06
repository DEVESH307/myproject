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

# Global dictionaries to store payment-related information
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

# Find the current card ID based on user input
def find_current_card_id(data, user_input):
    for conversation in data["Card"]:
        if user_input.lower() == conversation["user"].lower() or user_input == str(conversation["id"]):
            return conversation["id"]
    return None

# Get related option cards for a given card ID
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

# Get parent data for the current card ID == 0
def get_parent_data(data, current_card_id):
    # Get all the parent data for current_card_id = 0
    return get_related_cards(data, current_card_id)

# Check if a Company ID is valid.
def is_valid_company_id(company_id):
    # Check if a Company ID is valid.
    if len(company_id) < 10:
        return False, "Company ID should have at least 10 digits."
    
    return True, None

# Check if a Transaction ID is valid.
def is_valid_transaction_id(transaction_id):
    # Check if a Transaction ID is valid.
    if len(transaction_id) < 10:
        return False, "Transaction ID should have at least 10 digits."
    return True, None

# Check and update payment status information
def paymentStatus(user_input, current_card_id):
    # Initialize dictionaries to store payment status and response data
    payment_status_info = {
        "Company ID": None,
        "Transaction ID": None
    }
    
    response_data = {
        "current_card_id": None,
        "bot_reply": None,
        "is_valid_company": None,
        "is_valid_transaction": None
    }

    # Store the current card ID in the response data
    response_data["current_card_id"] = current_card_id

    # Check if the current card ID is 5
    if current_card_id == 5 and user_input:
        # Check the validity of the entered company ID
        is_valid_company, company_error_message = is_valid_company_id(user_input)
        
        # Store the validation result in the response data
        response_data["is_valid_company"] = is_valid_company
        
        if is_valid_company:
            # Store the valid company ID in payment status info
            payment_status_info["Company ID"] = user_input
        else:
            # Prepare bot reply for invalid company ID
            bot_reply = f"Sorry, you have entered an invalid Company ID. {company_error_message}"
            response_data['bot_reply'] = bot_reply
            response_data['user_input'] = user_input

    # Check if the current card ID is 6
    elif current_card_id == 6 and user_input:
        # Check the validity of the entered transaction ID
        is_valid_transaction, transaction_error_message = is_valid_transaction_id(user_input)
        
        # Store the validation result in the response data
        response_data["is_valid_transaction"] = is_valid_transaction
        
        if is_valid_transaction:
            # Store the valid transaction ID in payment status info
            payment_status_info["Transaction ID"] = user_input
            response_data["current_card_id"] = current_card_id
        else:
            # Prepare bot reply for invalid transaction ID
            bot_reply = f"Sorry, you have entered an invalid Transaction ID. {transaction_error_message}"
            response_data['bot_reply'] = bot_reply
            response_data['user_input'] = user_input
    
    # Return payment status info and response data
    return payment_status_info, response_data

# Check and update payment History information
def paymentHistory():
    pass

# Main logic for the conversational chatbot
def conversational_chatbot(user_input):
    global rule_based_triggered
    
    # Load cards data from a source
    cards_data = load_cards_data()
    
    # Get the current card ID
    current_card_id = 0
    
    # Retrieve parent data for the current card
    parent_data = get_parent_data(cards_data, current_card_id)
    
    # Define possible bot replies
    bot_replies = [
        "I apologize, but I don't have the information you're looking for.",
        "I'm sorry, I'm unable to understand. Please select from the given options.",
        # Add more bot replies here...
    ]
    
    # Choose a random bot reply
    bot_reply = random.choice(bot_replies)
    
    # Check if the rule-based mode is triggered
    if bot_reply == "I'm sorry, I'm unable to understand. Please select from the given options.":
        rule_based_triggered = True
        # Prepare JSON response with relevant information
        json_response = {
            'bot_reply': bot_reply,
            'parent_data': parent_data,
            'user_input': user_input
        }
        return json_response
    
    # Prepare JSON response with bot's reply and user input
    json_response = {
        'bot_reply': bot_reply,
        'user_input': user_input
    }
    
    return json_response

# Main logic for the Rule Based chatbot
def rule_based_chatbot(user_input):
    # Load cards data
    cards_data = load_cards_data()

    # Find the current card ID based on user input
    current_card_id = find_current_card_id(cards_data, user_input)

    # Retrieve the current card using the found card ID
    current_card = next(
        (card for card in cards_data["Card"] if card["id"] == current_card_id), None
    )

    if current_card:
        # Get the bot's reply from the current card
        bot_reply = current_card['chatbot']

        # Get related cards for context
        related_cards = get_related_cards(cards_data, current_card_id)

        # Prepare the response
        json_response = {
            'bot_reply': bot_reply,
            'related_cards': related_cards,
            'user_input': user_input
        }

        return json_response

    # Handle the case when the current card is not found
    json_response = {
        'bot_reply': "I'm sorry, I cannot understand that input.",
        'user_input': user_input
    }
    return json_response

# API view for getting bot replies
class GetBotReplyAPIView(APIView):
    # Handle GET requests to retrieve bot replies
    @csrf_exempt
    def get(self, request):
        user_input = request.GET.get('user_input', '').strip()

        global rule_based_triggered
        if rule_based_triggered:
            # Use rule-based chatbot for the initial response
            rule_based_response = rule_based_chatbot(user_input)
            
            if rule_based_response['bot_reply'] == "I'm sorry, I cannot understand that input.":
                rule_based_triggered = False
                # Use conversational chatbot if rule-based response is not informative
                conversational_response = conversational_chatbot(user_input)
                return JsonResponse(conversational_response, json_dumps_params={'indent': 4})
            
            return JsonResponse(rule_based_response, json_dumps_params={'indent': 4})
        else:
            # Use conversational chatbot
            conversational_response = conversational_chatbot(user_input)
            return JsonResponse(conversational_response, json_dumps_params={'indent': 4})
    
    # Handle POST requests to process user input and payment information
    @csrf_exempt
    def post(self, request):
        user_input = request.POST.get('user_input', '').strip()
        user_input_type = request.POST.get('user_input_type', '').strip()
        cards_data = load_cards_data()
        current_card_id = request.session.get('current_card_id', None)

        if user_input_type == "clickedCardMessage":
            # Process clicked card message
            current_card_id = find_current_card_id(cards_data, user_input)
            request.session['current_card_id'] = current_card_id
            return JsonResponse({
                'bot_reply': f"Clicked card {current_card_id}.",
                'user_input': user_input,
                'user_input_type': user_input_type
            }, json_dumps_params={'indent': 4})
        elif user_input_type == "userMessage":
            pass
        else:
            current_card_id = None
        
        try:
            if current_card_id == 5 or current_card_id == 6:
                # print(current_card_id)
                # Check payment status
                payment_status_info, payment_status_response = paymentStatus(user_input, current_card_id)
                
                if payment_status_response.get('is_valid_company') or payment_status_response.get('is_valid_transaction'):
                    return JsonResponse({
                        'bot_reply': "Please allow me a moment; I am in the process of fetching your Payment Status for the past month.",
                        'payment_status_response': payment_status_response,
                        'payment_status_info': payment_status_info
                    }, json_dumps_params={'indent': 4})
                else:
                    return JsonResponse({
                        'bot_reply': payment_status_response['bot_reply'],
                        'payment_status_info': payment_status_info
                    }, json_dumps_params={'indent': 4})
            else:
                raise ValueError("Invalid current_card_id")
        except ValueError as e:
            return JsonResponse({
                'bot_reply': str(e),
                'user_input_type': user_input_type,
                'user_input': user_input,
                'current_card_id': current_card_id
            }, status=400, json_dumps_params={'indent': 4})

