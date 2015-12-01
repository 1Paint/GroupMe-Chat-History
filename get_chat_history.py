import sys
import os
import time

from urllib2 import urlopen
from json import load

token = TOKEN
group_id = GROUP_ID
message_limit = 100  # cannot be greater than 100

url = "https://api.groupme.com/v3/groups/%i/messages" % group_id
url += "?token=%s" % token
url += "&limit=%i" % message_limit

def get_json(url):
    """Obtain information in JSON format."""
    response = urlopen(url)
    json_obj = load(response)
        
    return json_obj

def get_chat_history(json, old_date):
    """
    Retrieve and write down all dates, times, names, and messages in a
    groupme group chat. Messages are retrieved in reverse-chronological
    order---the most recent messages are retrieved first.

    Messages are retrieved in sets. The amount of messages per set is
    equal to 'message_limit'. 

    An 'IndexError' is raised when the total number of messages in the
    group chat is not a multiple of 'message_limit'. To illustrate: if
    the total number of messages in the group chat is 257 and the
    'message_limit' is 100, the final set of messages contains 57
    messages (257 mod 100). These 57 messages are obtained when
    iterating from i = 0-56. An attempt to obtain the 58th message
    corresponding to i = 57 raises the 'IndexError.' This indicates that
    the earliest message in the group chat has been retrieved. The date
    of the group's creation is then written.
    """
    try:
        for i in range(message_limit):
            
            # Parse the data and retrieve times, names, and messages.
            epoch_time = json['response']['messages'][i]['created_at']
            date = time.strftime('%d %b %Y', time.localtime(epoch_time))
            hour = time.strftime('%H:%M:%S', time.localtime(epoch_time))

            name = json['response']['messages'][i]['name']
            text = json['response']['messages'][i]['text']
            line = '*%s* **%s**: %s\n\n' % (hour, name, text)

            # Separate messages by date.
            if date != old_date:
                f.write('=======\n%s\n' % old_date)
                old_date = date

            # Write times, names, and messages.
            f.write(line.encode('ascii', 'ignore'))

            # Iterate through the next set of messages.
            if i == message_limit-1:
                before_id = json['response']['messages'][i]['id']
                next_url = "%s&before_id=%s" % (url, before_id)
                next_json_obj = get_json(next_url)
                get_chat_history(next_json_obj, old_date)
                
    except IndexError:
        f.write('=======\n%s\n' % old_date)  # date of group creation

def reverse():
    """Order messages from earliest to most recent, top to bottom."""
    f = open(('%i_history.txt' % group_id), 'r')
    final = open(('%i_chat_history.md' % group_id), 'w')

    # Correctly order the messages.
    for line in reversed(f.readlines()):
        final.write(line)

    f.close()
    final.close()
    os.remove('%i_history.txt' % group_id)  # delete reversed-chat file

if __name__ == '__main__':
    f = open(('%i_history.txt' % group_id), 'w')
    
    initial_json = get_json(url)
    initial_time = initial_json['response']['messages'][0]['created_at']
    initial_date = time.strftime('%d %b %Y', time.localtime(initial_time))
    
    get_chat_history(initial_json, initial_date)
    
    f.close()
    reverse()
    

