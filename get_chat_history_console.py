"""
This script retrieves the chat histories of a user when given the
user's access token. This script interacts with the user via the
console.

Users can obtain access tokens at https://dev.groupme.com/ by logging
in and clicking 'Access Token' at the top right of the page.

Upon being given an access token, the application communicates with
GroupMe's public API (https://dev.groupme.com/docs/v3) and lists all
current group and direct message chats of the access token's owner.
The user can then input a chat's type and its ID to retrieve its
history. The application estimates the runtime upon retrieval.

Chat histories are retrieved with the most recent messages being
obtained first---Messages are thus written in reverse-chronological
order, top to bottom. These messages are put into a temporary text
file before being written in chronological order into an HTML file.
The temporary text file is then deleted and a CSS file is created 
to format the HTML file for readability.
"""

import os
import time

import urllib2
from json import load

message_limit = 100  # cannot be greater than 100

def get_URL(token, chat_type, chat_ID):
    """Retrieve the URL given an access token, chat type, and an ID."""
    if chat_type == 'group':
        url = 'https://api.groupme.com/v3/groups/%s/messages' % chat_ID
        url += "?token=%s" % token
    elif chat_type == 'direct':
        url = 'https://api.groupme.com/v3/direct_messages'
        url += '?other_user_id=%s' % chat_ID
        url += "&token=%s" % token

    url += "&limit=%i" % message_limit
    
    return url

def get_json(url):
    """Retrieve the JSON response from an API."""
    response = urllib2.urlopen(url)
    json = load(response)
    
    return json

def get_self_id(token):
    """Obtain a user's ID given their token."""
    url = "https://api.groupme.com/v3/users/me?token=%s" % token
    json = get_json(url)
    user_id = json['response']['user_id']

    return user_id
    
def get_groups(token):
    """Return a list of group chats' IDs and names."""
    url = 'https://api.groupme.com/v3/groups?token=%s' % token
    json = get_json(url)
    response = json['response']
    
    groups = []
    for i in response:
        ID = i['id']
        name = i['name']
        groups.append([ID, name])

    return groups
    
def get_directs(token):
    """Return a list of direct message chats' IDs and names."""
    url = 'https://api.groupme.com/v3/chats?token=%s' % token
    json = get_json(url)
    response = json['response']
    
    directs = []
    for i in response:
        ID = i['other_user']['id']
        name = i['other_user']['name']
        directs.append([ID, name])

    return directs
    
def create_history(json, old_date, self_id, url, chat_type, f):
    """
    Create a temporary chat history file.
    
    Retrieve and write down all dates, times, names, and messages in a
    groupme group chat. Messages are retrieved in reverse-chronological
    order---the most recent messages are retrieved first. The file is
    formatted in HTML and pairs with a corresponding CSS file.

    Parameters:
        json: The GroupMe API response in JSON format.
        old_date: The date of the most recent message.
        self_id: The user's GroupMe ID.
        url: The URL being worked with.
        chat_type: The type of chat---'group' or 'direct'.
        f: The temporary file being written to.

    Messages are retrieved in sets. The amount of messages per set is
    equal to 'message_limit'. 

    An 'IndexError' is raised when the total number of messages in the
    group chat is not a multiple of 'message_limit'. To illustrate: if
    the total number of messages in the group chat is 257 and the
    'message_limit' is 100, the final set of messages contains 57
    messages (257 mod 100). These 57 messages are obtained when
    iterating from i = 0-56. An attempt to obtain the 58th message
    corresponding to i = 57 raises the 'IndexError.' This indicates 
    that the earliest message in the group chat has been retrieved. The
    date of the group's creation is then written.
    """
    if chat_type == 'group':
        msg = 'messages'
    elif chat_type == 'direct':
        msg = 'direct_messages'
        
    try:
        for i in range(message_limit):
            # Parse the data and retrieve times, names, and messages.
            epoch_time = json['response'][msg][i]['created_at']
            date = time.strftime('%A, %d %B %Y', time.localtime(epoch_time))

            user_id = json['response'][msg][i]['user_id']
            name = json['response'][msg][i]['name']
            hour = time.strftime('%H:%M:%S', time.localtime(epoch_time))
            text = json['response'][msg][i]['text']
            if text: text = text.encode('unicode-escape')  # escape \n, etc.

            # Format into HTML.
            if user_id == self_id:
                name = '<td class="self_name">%s</td>' % name
                hour = '<td class="self_hour">(%s):</td>' % hour
            else:
                name = '<td class="name">%s</td>' % name
                hour = '<td class="hour">(%s):</td>' % hour
            text = '<td class="text">%s</td>' % text
            line = '<tr>%s %s %s</tr>\n' % (name, hour, text)

            # Separate messages by date.
            if date != old_date:
                f.write('<tr>')
                f.write('<td class="date" colspan="3">%s</td>' % old_date)
                f.write('</tr>\n')
                old_date = date

            # Write down times, names, and messages.
            f.write(line.encode('UTF-8', 'replace'))

            # Iterate through the next set of messages.
            if i == message_limit-1:
                before_id = json['response'][msg][i]['id']
                next_url = "%s&before_id=%s" % (url, before_id)
                next_json = get_json(next_url)
                create_history(next_json, old_date, self_id, url, chat_type, f)
                
    except IndexError:
        # Finally, write the group creation date.
        f.write('<tr><td class="date" colspan="3">%s</td></tr>' % old_date)    
        
def format_history(chat_type, chat_ID):
    """
    Add HTML headers and footers and order messages from earliest to
    most recent, top to bottom. Reference the HTML file to a CSS file.
    """
    f = open(('%s_chat_history.txt' % chat_ID), 'r')
    final = open(('%s_%s_chat_history.html' % (chat_ID, chat_type)), 'w')

    # Create the header and reference the CSS file.
    header = (
        '<!DOCTYPE html>\n<html>\n<body>\n'
        '<head>\n'
        '<link rel="stylesheet" href="styles.css" type="text/css">\n'
        '</head>\n'
        '<table>\n')
    final.write(header)

    # Correctly order the messages.
    for line in reversed(f.readlines()):
        final.write(line)

    # Close out HTML formatting.
    footer = '</table>\n</body>\n</html>'
    final.write(footer)

    f.close()
    final.close()
    os.remove('%s_chat_history.txt' % chat_ID)  # Remove text file.
    
def create_css():
    """Create a CSS file to format the HTML file."""
    if not os.path.isfile('styles.css'):
        f = open('styles.css', 'w')
        f.write(
            'body {\n'
            '    font-family: Arial, serif;\n'
            '}\n')
        f.write(
            'table {\n'
            '    table-layout: fixed;\n'  # scale to browser width
            '}\n')
        f.write(
            'td.date {\n'
            '    font-size: 140%;\n'
            '    font-weight: 600;\n'
            '    color: #FFFFFF;\n'
            '    padding-left: 4px;\n'
            '    background: #696969;\n'
            '}\n')
        f.write(
            'td.self_name {\n'
            '    font-size: 11pt;\n'
            '    font-weight: bold;\n'
            '    color: #00CC00;\n'
            '    text-align: right;\n'
            '    vertical-align: text-top;\n'
            '    padding-left: 20px;\n'
            '    padding-top: 3px;\n'
            '    padding-bottom: 3px;\n'
            '    white-space: nowrap;\n'
            '}\n')
        f.write(
            'td.self_hour {\n'
            '    font-size: 11pt;\n'
            '    font-weight: bold;\n'
            '    color: #00CC00\n;'
            '    padding-top: 3px;\n'
            '    padding-bottom: 3px;\n'
            '    vertical-align: text-top;\n'
            '}\n')
        f.write(
            'td.name {\n'
            '    font-size: 11pt;\n'
            '    font-weight: bold;\n'
            '    color: #6495ED;\n'
            '    text-align: right;\n'
            '    vertical-align: text-top;\n'
            '    padding-left: 20px;\n'
            '    padding-top: 3px;\n'
            '    padding-bottom: 3px;\n'
            '    white-space: nowrap;\n'
            '}\n')
        f.write(
            'td.hour {\n'
            '    font-size: 11pt;\n'
            '    font-weight: bold;\n'
            '    color: #6495ED;\n'
            '    padding-top: 3px;\n'
            '    padding-bottom: 3px;\n'
            '    vertical-align: text-top;\n'
            '}\n')
        f.write(
            'td.text {\n'
            '    font-size: 11pt;\n'
            '    word-break: break-word;\n'  # wrap long messages
            '}\n')
        f.close()

def check_token(token):
    """Check the validity of the access token."""
    try:
        get_self_id(token)
        valid = True
    except:
        valid = False
        
    return valid
    
def get_token():
    """Obtain the user's token from the console."""
    token = raw_input("Enter your 'Access Token': ")
    
    while check_token(token) == False:
        print "Token is invalid."
        token = raw_input("Enter your 'Access Token': ")
    
    return token

def get_chat_info(token):
    """Obtain the chat type and ID to retrieve the chat history."""
    # Obtain the chat type from the user.
    chat_type = raw_input("\nType in the chat type of the chat you want "
                            "to obtain ('group' or 'direct'): ")
    while chat_type.lower() != 'direct' and chat_type.lower() != 'group':
        print "Please enter 'group' or 'direct', without the single quotes."
        chat_type = raw_input("Type in the chat type of the chat you " 
                                "want to obtain: ")
    
    # Obtain the chat ID from the user and retrieve the chat history.
    while True:
        try: 
            chat_ID = raw_input("Enter the chat ID of the chat or 'back' "
                                "to change the chat type: ")
            if chat_ID == 'back':
                break
            else:
                print "Please wait..."
                get_chat(token, chat_type, chat_ID)
                print "Done."
                break
        except:
            print "The chat ID entered is invalid. Type in an ID or 'back'."
         
    get_chat_info(token)
    
def list_chats(token):
    """Find and list the chats available."""
    # Obtain a list of chats for the user of the access token.
    groups = get_groups(token)
    directs = get_directs(token)
    attributes = ['ID', 'Name']
    
    col_width = max(len(group[0]) for group in groups) + 2
    print "\nGroup Chats:"
    print "".join(i.ljust(col_width) for i in attributes)
    for group in groups:
        print "".join(data.ljust(col_width) for data in group)
    
    col_width = max(len(direct[0]) for direct in directs) + 2
    print "\nDirect Message Chats:"
    print "".join(i.ljust(col_width) for i in attributes)
    for direct in directs:
        print "".join(data.ljust(col_width) for data in direct)
    
def get_runtime(msg_count):
    """
    Estimate the time to retrieve the chat history based on the
    number of messages in the selected chat.
    """
    seconds = msg_count/360  # based on tests; 360 messages ~= 1 second
    minutes = seconds/60
    seconds = seconds % 60
    
    runtime = ("Estimated Runtime: %i minutes %i seconds..."
        % (minutes, seconds))

    print runtime
        
def get_chat(token, chat_type, chat_ID):
    """
    Obtain the requested chat history and store it in a formatted HTML
    file with CSS.
    """
    # Obtain the relevant URL.
    url = get_URL(token, chat_type, chat_ID)
    
    if chat_type == 'group':
        msg = 'messages'
    elif chat_type == 'direct':
        msg = 'direct_messages'
    
    # Obtain the most recent message date as a starting reference.
    i_json = get_json(url)
    i_time = i_json['response'][msg][0]['created_at']
    i_date = time.strftime('%A, %d %B %Y', time.localtime(i_time))
    
    # Estimate the runtime.
    msg_count = i_json['response']['count']
    get_runtime(msg_count)
        
    # Obtain the user's ID to color the user's name in the chat file.
    self_id = get_self_id(token)

    # Create the chat history as an HTML file and format it.
    f = open(('%s_chat_history.txt' % chat_ID), 'w')
    create_history(i_json, i_date, self_id, url, chat_type, f)
    f.close()
    format_history(chat_type, chat_ID)
    create_css()
           
if __name__ == '__main__':
    
    token = get_token()
    list_chats(token)
    get_chat_info(token)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
