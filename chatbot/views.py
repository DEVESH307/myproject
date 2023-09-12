import os
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.templatetags.static import static
from rest_framework.views import APIView
from rest_framework.response import Response
import random
import pandas as pd
from pandasql import sqldf
from datetime import datetime, timedelta


# Global flag to control the chatbot behavior
rule_based_triggered = False

# Global dictionaries to store payment-related information
payment_status_info = {
    "Company ID": None,
    "Transaction ID": None
}
payment_status_response_data = {
    "current_card_id": None,
    "bot_reply": None,
    "is_valid_company": None,
    "is_valid_transaction": None
} 

payment_history_info = {
    "Company ID": None,
    "Date Range": {
        "Start Date": None,
        "End Date": None
    },
    "Time Period": None
}
payment_history_response_data = {
    "current_card_id": None,
    "bot_reply": None,
    "is_valid_company": None,
    "is_valid_date_range": None,
    "is_valid_time_period": None
}

# Read the csv file using pandas
csv_data_path = os.path.join(os.path.dirname(__file__), 'static/chatbot/data/data.csv')
dataframe = pd.read_csv(csv_data_path)
dataframe['trn_date'] = pd.to_datetime(dataframe['trn_date'], format='%d-%m-%Y').dt.strftime('%Y%m%d')
# print(dataframe)


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
    try:
        # Attempt to convert the company_id to an integer
        company_id_int = int(company_id)
        
        # Check if the length of the converted integer is less than 10 digits
        if len(str(company_id_int)) < 10:
            raise ValueError("Company ID should have at least 10 digits.")
        
        # If no exceptions are raised, the company ID is valid
        return True, None

    except ValueError as e:
        # Handle the ValueError exception and return an error message
        return False, str(e)


# Check if a Transaction ID is valid.
def is_valid_transaction_id(transaction_id):
    try:        
        # Check if the length of the converted integer is less than 10 digits
        if len(str(transaction_id)) < 10:
            raise ValueError("Transaction ID should have at least 10 digits.")
        
        # If no exceptions are raised, the transaction ID is valid
        return True, None

    except ValueError as e:
        # Handle the ValueError exception and return an error message
        return False, str(e)
  

# Check if a Date Range is valid for payment history.
def is_valid_date_range(user_input):
    if not isinstance(user_input, dict):
        return False, "Error: Input must be a dictionary."

    start_date_str = user_input.get('startDate')
    end_date_str = user_input.get('endDate')

    if start_date_str is None or end_date_str is None:
        return False, "Error: 'startDate' and 'endDate' keys are required in the input dictionary."

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        today = datetime.now()
        six_months_ago = today - timedelta(days=180)

        if start_date < end_date and six_months_ago <= start_date <= today and end_date <= today:
            return True, None
        else:
            return False, "Date range is not valid."

    except ValueError:
        return False, "Error: Date format is not valid or one of the dates is not a valid calendar date."


# Check if a time period is valid for payment history.
def is_valid_time_period(time_period):
    try:
        # Check if the time period is 1, 3, or 6
        if time_period in [1, 3, 6, '1', '3', '6']:
            return True, None  # Return True and no error message for valid time periods

        return False, "Error: You have entered an invalid time period. It should be 1, 3, or 6."

    except Exception:
        return False, "Error: An unexpected error occurred."
    

# Check and update payment status information
def get_payment_status_data_dictionary(user_input, current_card_id):
    # Use the global variable
    global payment_status_info  
    global payment_status_response_data 

    # Reset all entries to None if current_card_id is 5
    if current_card_id == 5 and user_input:
        payment_status_info = {
            "Company ID": None,
            "Transaction ID": None
        }
        payment_status_response_data = {
            "current_card_id": None,
            "bot_reply": None,
            "is_valid_company": None,
            "is_valid_transaction": None
        } 

    # Store the current card ID in the response data
    payment_status_response_data["current_card_id"] = current_card_id

    # Check if the current card ID is 5
    if current_card_id == 5 and user_input:
        # Check the validity of the entered company ID
        is_valid_company, company_error_message = is_valid_company_id(user_input)
        
        # Store the validation result in the response data
        payment_status_response_data["is_valid_company"] = is_valid_company
        
        if is_valid_company:
            # Store the valid company ID in payment status info
            payment_status_info["Company ID"] = user_input
        else:
            # Prepare bot reply for invalid company ID
            bot_reply = f"Sorry, you have entered an invalid Company ID. {company_error_message}"
            payment_status_response_data['bot_reply'] = bot_reply
            payment_status_response_data['user_input'] = user_input

    # Check if the current card ID is 6
    elif current_card_id == 6 and user_input:
        payment_status_info['Company ID'] = None
        payment_status_response_data['is_valid_company'] = None
        # Check the validity of the entered transaction ID
        is_valid_transaction, transaction_error_message = is_valid_transaction_id(user_input)
        
        # Store the validation result in the response data
        payment_status_response_data["is_valid_transaction"] = is_valid_transaction
        
        if is_valid_transaction:
            # Store the valid transaction ID in payment status info
            payment_status_info["Transaction ID"] = user_input
            payment_status_response_data["current_card_id"] = current_card_id
        else:
            # Prepare bot reply for invalid transaction ID
            bot_reply = f"Sorry, you have entered an invalid Transaction ID. {transaction_error_message}"
            payment_status_response_data['bot_reply'] = bot_reply
            payment_status_response_data['user_input'] = user_input
    
    # Return payment status info and response data
    return payment_status_info, payment_status_response_data


#payment status function
def get_payment_status(payment_status_info):
    try:
        company_id = payment_status_info.get('Company ID')
        transaction_id = payment_status_info.get('Transaction ID')
        query = "SELECT * FROM dataframe WHERE "
        if company_id:
            query += f"client_id = '{company_id}'"
        elif transaction_id:
            query += f"trn_number = '{transaction_id}'"
        else:
            return "Invalid Company ID or Transaction ID has been provided."
        query += " ORDER BY trn_date DESC LIMIT 10"
        result = sqldf(query)
        return result
    except Exception as e:
        return f"An error occurred: {str(e)}"


# # Check and update payment history information
# def get_payment_history_data_dictionary(user_input, current_card_id):
#     # Use the global variable
#     global payment_history_info
#     global payment_history_response_data

#     # Reset all entries to None if current_card_id is 7
#     if current_card_id == 7 and user_input:
#         payment_history_info = {
#             "Company ID": None,
#             "Date Range": {
#                 "Start Date": None,
#                 "End Date": None
#             },
#             "Time Period": None
#         }
#         payment_history_response_data = {
#             "current_card_id": None,
#             "bot_reply": None,
#             "is_valid_company": None,
#             "is_valid_date_range": None,
#             "is_valid_time_period": None
#         }

#     # Store the current card ID in the response data
#     payment_history_response_data["current_card_id"] = current_card_id

#     # Update the dictionary based on the user_input and current card id
#     if current_card_id == 7 and user_input:
#         # Check the validity of the entered company ID
#         is_valid_company, company_error_message = is_valid_company_id(user_input)
        
#         # Store the validation result in the response data
#         payment_history_response_data["is_valid_company"] = is_valid_company
        
#         if is_valid_company:
#             # Store the valid company ID in payment status info
#             payment_history_info["Company ID"] = user_input
#         else:
#             # Prepare bot reply for invalid company ID
#             bot_reply = f"Sorry, you have entered an invalid Company ID. {company_error_message}"
#             payment_history_response_data['bot_reply'] = bot_reply
#             payment_history_response_data['user_input'] = user_input
#     elif current_card_id == 8 and user_input:
#         # Convert the JSON string to a Python dictionary
#         user_input = json.loads(user_input)
#         print(user_input)
#         # Reset the time period and validity of time period
#         payment_history_info['Time Period'] = None
#         payment_history_response_data['is_valid_time_period'] = None

#         # Check the validity of the entered date range
#         is_valid_date_range_result, date_range_error_message = is_valid_date_range(user_input)
        
#         # Store the validation result in the response data
#         payment_history_response_data["is_valid_date_range"] = is_valid_date_range_result
        
#         if is_valid_date_range_result:
#             payment_history_info["Date Range"]["Start Date"] = user_input["startDate"]
#             payment_history_info["Date Range"]["End Date"] = user_input["endDate"]
#         else:
#             # Prepare bot reply for invalid date range
#             bot_reply = f"Sorry, the entered date range is not valid. {date_range_error_message}"
#             payment_history_response_data['bot_reply'] = bot_reply
#             payment_history_response_data['user_input'] = user_input
#     elif current_card_id in [10, 11, 12] and user_input:
#         # Reset Date Range and validity of Date Range
#         payment_history_info["Date Range"]["Start Date"] = None
#         payment_history_info["Date Range"]["End Date"] = None
#         payment_history_response_data['is_valid_date_range'] = None

#         # Check the validity of the entered time period
#         is_valid_time_period_result, time_period_error_message = is_valid_time_period(user_input)
        
#         # Store the validation result in the response data
#         payment_history_response_data["is_valid_time_period"] = is_valid_time_period_result
        
#         if is_valid_time_period_result:
#             time_period = user_input
#             payment_history_info["Time Period"] = time_period
#         else:
#             # Prepare bot reply for invalid time period
#             bot_reply = f"Sorry, you have entered an invalid time period. {time_period_error_message}"
#             payment_history_response_data['bot_reply'] = bot_reply
#             payment_history_response_data['user_input'] = user_input
#     return payment_history_info, payment_history_response_data

# Check and update payment history information
def get_payment_history_data_dictionary(user_input, current_card_id):
    # Use the global variable
    global payment_history_info
    global payment_history_response_data

    # Reset all entries to None if current_card_id is 7
    if current_card_id == 7 and user_input:
        payment_history_info = {
            "Company ID": None,
            "Date Range": {
                "Start Date": None,
                "End Date": None
            },
            "Time Period": None
        }
        payment_history_response_data = {
            "current_card_id": None,
            "bot_reply": None,
            "is_valid_company": None,
            "is_valid_date_range": None,
            "is_valid_time_period": None
        }

    # Store the current card ID in the response data
    payment_history_response_data["current_card_id"] = current_card_id

    # Update the dictionary based on the user_input and current card id
    if current_card_id == 7 and user_input:
        # Check the validity of the entered company ID
        is_valid_company, company_error_message = is_valid_company_id(user_input)
        
        # Store the validation result in the response data
        payment_history_response_data["is_valid_company"] = is_valid_company
        
        if is_valid_company:
            # Store the valid company ID in payment status info
            payment_history_info["Company ID"] = user_input
        else:
            # Prepare bot reply for invalid company ID
            bot_reply = f"Sorry, you have entered an invalid Company ID. {company_error_message}"
            payment_history_response_data['bot_reply'] = bot_reply
            payment_history_response_data['user_input'] = user_input
    elif current_card_id == 8 and user_input:
        # Convert the JSON string to a Python dictionary
        user_input = json.loads(user_input)
        print(type(user_input))
        # Reset the time period and validity of time period
        payment_history_info['Time Period'] = None
        payment_history_response_data['is_valid_time_period'] = None

        # Check the validity of the entered date range
        is_valid_date_range_result, date_range_error_message = is_valid_date_range(user_input)
        
        # Store the validation result in the response data
        payment_history_response_data["is_valid_date_range"] = is_valid_date_range_result
        
        if is_valid_date_range_result:
            payment_history_info["Date Range"]["Start Date"] = user_input["startDate"]
            payment_history_info["Date Range"]["End Date"] = user_input["endDate"]
        else:
            # Prepare bot reply for invalid date range
            bot_reply = f"Sorry, the entered date range is not valid. {date_range_error_message}"
            payment_history_response_data['bot_reply'] = bot_reply
            payment_history_response_data['user_input'] = user_input
    elif current_card_id in [10, 11, 12] and user_input:
        # Reset Date Range and validity of Date Range
        payment_history_info["Date Range"]["Start Date"] = None
        payment_history_info["Date Range"]["End Date"] = None
        payment_history_response_data['is_valid_date_range'] = None

        # Check the validity of the entered time period
        is_valid_time_period_result, time_period_error_message = is_valid_time_period(user_input)
        
        # Store the validation result in the response data
        payment_history_response_data["is_valid_time_period"] = is_valid_time_period_result
        
        if is_valid_time_period_result:
            time_period = user_input
            payment_history_info["Time Period"] = time_period
        else:
            # Prepare bot reply for invalid time period
            bot_reply = f"Sorry, you have entered an invalid time period. {time_period_error_message}"
            payment_history_response_data['bot_reply'] = bot_reply
            payment_history_response_data['user_input'] = user_input
    return payment_history_info, payment_history_response_data


#payment history function
def get_payment_history(payment_history_info):
    try:
        company_id = payment_history_info.get('Company ID')
        date_range = payment_history_info.get('Date Range')
        time_period = payment_history_info.get('Time Period')

        startDate = date_range.get('Start Date')
        endDate = date_range.get('End Date')

        if startDate and endDate:
            startDate = datetime.strptime(startDate, '%Y-%m-%d').strftime('%Y%m%d')
            endDate = datetime.strptime(endDate, '%Y-%m-%d').strftime('%Y%m%d')
        elif startDate and not endDate:
            startDate = datetime.strptime(startDate, '%Y-%m-%d').strftime('%Y%m%d')
            endDate = datetime.today().strftime('%Y%m%d')
        elif time_period:
            endDate = datetime.today().strftime('%Y%m%d')
            startDate = (datetime.today() - timedelta(days=int(time_period)*30)).strftime('%Y%m%d')
        else:
            return "Invalid input. Please provide valid Company ID, Date Range, or Time Period."

        # query = (
        #     f"SELECT client_id, client_name, trn_number as transaction_number, "
        #     f"trn_date as transaction_date, amt as amount FROM dataframe WHERE "
        #     f"client_id='{company_id}' AND trn_date BETWEEN '{startDate}' AND '{endDate}' "
        #     f"ORDER BY transaction_date"
        # )
        query = f"SELECT * FROM dataframe WHERE client_id='{company_id}' AND trn_date BETWEEN '{startDate}' AND '{endDate}'"


        # Execute the query
        result = sqldf(query)

        return result

    except Exception as e:
        return f"An error occurred: {str(e)}"


# Function to generate the bot's reply with a table view
def generate_bot_reply_table_view(sql_query_dataframe):
    try:
        if isinstance(sql_query_dataframe, pd.DataFrame):
            if not sql_query_dataframe.empty:
                # Generate the HTML table with custom styling
                table_html = sql_query_dataframe.to_html(
                    classes=['table', 'table-bordered', 'table-striped', 'table-responsive'],
                    index=False
                )
                # Create a bot message
                bot_message = "Here is your payment status for the last month:"
                # The URL path to your CSS file
                custom_css_path = '/static/chatbot/css/style.css'  
                # Combine the bot message, custom CSS (loaded from the CSS file), and the table HTML
                bot_reply = (
                    f'<div class="bot-message">{bot_message}</div>'
                    f'<link rel="stylesheet" type="text/css" href="{custom_css_path}">'
                    f'<div class="table-responsive">{table_html}</div>'
                )
                return bot_reply
    except Exception as e:
        return f"An error occurred: {str(e)}"

    return None


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
                'bot_reply': f"Clicked on {user_input}.",
                'user_input': user_input,
                'user_input_type': user_input_type
            }, json_dumps_params={'indent': 4})
        elif user_input_type == "userMessage":
            pass
        else:
            current_card_id = None
        
        try:
            if current_card_id in [5, 6]:
                # print(current_card_id)
                # Check payment status
                payment_status_info, payment_status_response = get_payment_status_data_dictionary(user_input, current_card_id)
                
                if payment_status_response.get('is_valid_company') or payment_status_response.get('is_valid_transaction'):
                    payment_status_dataframe = get_payment_status(payment_status_info)
                    # Check if the result is a DataFrame or an error message
                    bot_reply = generate_bot_reply_table_view(payment_status_dataframe)

                    if bot_reply:
                        return JsonResponse({
                            'bot_reply': bot_reply,
                            'payment_status_response': payment_status_response,
                            'payment_status_info': payment_status_info
                        }, json_dumps_params={'indent': 4})
                    else:
                        return JsonResponse({
                            'bot_reply': 'You have entered invalid Company ID or Transaction ID'
                        }, json_dumps_params={'indent': 4})
                else:
                    return JsonResponse({
                        'bot_reply': payment_status_response['bot_reply'],
                        'payment_status_info': payment_status_info,
                        'payment_status_response': payment_status_response
                    }, json_dumps_params={'indent': 4})
                
            elif current_card_id == 7:
                payment_history_info, payment_history_response = get_payment_history_data_dictionary(user_input, current_card_id)
                if payment_history_response.get('is_valid_company'):
                    return JsonResponse({
                            'bot_reply': 'you have entered valid company id',
                            'payment_history_info': payment_history_info,
                            'payment_history_response': payment_history_response
                        }, json_dumps_params={'indent': 4})
                else:
                    return JsonResponse({
                            'bot_reply': payment_history_response['bot_reply'],
                            'payment_history_info': payment_history_info,
                            'payment_history_response': payment_history_response
                        }, json_dumps_params={'indent': 4})

            elif current_card_id == 8:
                payment_history_info, payment_history_response = get_payment_history_data_dictionary(user_input, current_card_id)
                if payment_history_response.get('is_valid_date_range'):
                    payment_history_dataframe = get_payment_history(payment_history_info)
                    # Check if the result is a DataFrame or an error message
                    bot_reply = generate_bot_reply_table_view(payment_history_dataframe)

                    if bot_reply:
                        return JsonResponse({
                                'bot_reply': bot_reply,
                                'payment_history_info': payment_history_info,
                                'payment_history_response': payment_history_response
                            }, json_dumps_params={'indent': 4})
                    else:
                        return JsonResponse({
                            'bot_reply': 'You have entered invalid Company ID or Date Range'
                        }, json_dumps_params={'indent': 4})
                else:
                    return JsonResponse({
                            'bot_reply': payment_history_response['bot_reply'],
                            'payment_history_info': payment_history_info,
                            'payment_history_response': payment_history_response
                        }, json_dumps_params={'indent': 4})
                
            elif current_card_id in [10, 11, 12]:
                payment_history_info, payment_history_response = get_payment_history_data_dictionary(user_input, current_card_id)
                if payment_history_response.get('is_valid_time_period'):
                    payment_history_dataframe = get_payment_history(payment_history_info)
                    # Check if the result is a DataFrame or an error message
                    bot_reply = generate_bot_reply_table_view(payment_history_dataframe)

                    if bot_reply:
                        return JsonResponse({
                                'bot_reply': bot_reply,
                                'payment_history_info': payment_history_info,
                                'payment_history_response': payment_history_response
                            }, json_dumps_params={'indent': 4})
                    else:
                        return JsonResponse({
                            'bot_reply': 'You have entered invalid Company ID or Time Period'
                        }, json_dumps_params={'indent': 4})
                else:
                    return JsonResponse({
                            'bot_reply': payment_history_response['bot_reply'],
                            'payment_history_info': payment_history_info,
                            'payment_history_response': payment_history_response
                        }, json_dumps_params={'indent': 4})
                
            else:
                raise ValueError("Invalid current_card_id")
        except ValueError as e:
            return JsonResponse({
                'bot_reply': str(e),
                'user_input_type': user_input_type,
                'user_input': user_input,
                'current_card_id': current_card_id
            }, json_dumps_params={'indent': 4})

