# 1 second ~ 360 messages

import sys
import os
import time

import urllib2
from json import load

from PyQt4 import QtGui, QtCore

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
    corresponding to i = 57 raises the 'IndexError.' This indicates that
    the earliest message in the group chat has been retrieved. The date
    of the group's creation is then written.
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
    header = ('<!DOCTYPE html>\n<html>\n<body>\n'
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
    os.remove('%s_chat_history.txt' % chat_ID)
    create_css()
    
def create_css():
    """Create a CSS file to format the HTML file."""
    if not os.path.isfile('styles.css'):
        f = open('styles.css', 'w')
        f.write('body {\n'
                '    font-family: Arial, serif;\n'
                '}\n')
        f.write('table {\n'
                '    table-layout: fixed;\n'  # scale to browser width
                '}\n')
        f.write('td.date {\n'
                '    font-size: 140%;\n'
                '    font-weight: 600;\n'
                '    color: #FFFFFF;\n'
                '    padding-left: 4px;\n'
                '    background: #696969;\n'
                '}\n')
        f.write('td.self_name {\n'
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
        f.write('td.self_hour {\n'
                '    font-size: 11pt;\n'
                '    font-weight: bold;\n'
                '    color: #00CC00\n;'
                '    padding-top: 3px;\n'
                '    padding-bottom: 3px;\n'
                '    vertical-align: text-top;\n'
                '}\n')
        f.write('td.name {\n'
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
        f.write('td.hour {\n'
                '    font-size: 11pt;\n'
                '    font-weight: bold;\n'
                '    color: #6495ED;\n'
                '    padding-top: 3px;\n'
                '    padding-bottom: 3px;\n'
                '    vertical-align: text-top;\n'
                '}\n')
        f.write('td.text {\n'
                '    font-size: 11pt;\n'
                '    word-break: break-word;\n'  # wrap long messages
                '}\n')
        f.close()
    
class AppWindow(QtGui.QDialog):
    """This is the main application window users interact with."""
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setFixedWidth(350)  
        self.list_exists = False  # no chat lists have yet been retrieved
        
        self.layout = QtGui.QVBoxLayout()

        token_label = QtGui.QLabel("Access Token")
        self.token = QtGui.QLineEdit()
        self.token.setFixedWidth(250)
        token_line = QtGui.QHBoxLayout()
        token_line.addWidget(token_label)
        token_line.addWidget(self.token)
        
        find_button = QtGui.QPushButton('Find Chats')
        find_button.clicked.connect(self.find_chats)
        cancel_button = QtGui.QPushButton('Cancel')
        cancel_button.clicked.connect(self.cancel)
        
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton(find_button, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(cancel_button, QtGui.QDialogButtonBox.ActionRole)
        
        button_line = QtGui.QHBoxLayout()
        button_line.addStretch(0)
        button_line.addWidget(buttonBox)
        button_line.addStretch(0)
                
        self.layout.addLayout(token_line)
        self.layout.addLayout(button_line)
        
        self.setLayout(self.layout)
        
    def check_token(self, token):
        """Check the validity of the access token."""
        try:
            get_self_id(token)
            valid = True
        except:
            valid = False
            
        return valid
    
    def find_chats(self):
        """Obtain and format the chat log."""   
        self.setWindowTitle("Loading...")
            
        token = str(self.token.text())  # obtain user-inputted token
        self.token_str = token
        valid = self.check_token(token)
        
        # Find all chats if the given token is valid.
        if valid == False:
            self.setWindowTitle("Please Check Your Access Token")
        elif valid == True:
            self.setWindowTitle("Select Chat History to Retrieve")
            # Remove the current chat list if one already exists.
            if self.list_exists:
                self.layout.removeWidget(self.group_list)
                self.layout.removeWidget(self.direct_list)
                
            # Create the list group chats.
            self.group_list = QtGui.QListWidget()
            self.group_list.setFixedHeight(100)
            
            self.groups = get_groups(token)
            for i in self.groups:
                item = QtGui.QListWidgetItem(i[1])
                self.group_list.addItem(item)
   
            # Create the list of direct messaging chats.
            self.direct_list = QtGui.QListWidget()
            self.direct_list.setFixedHeight(100)
            
            self.directs = get_directs(token)
            for i in self.directs:
                item = QtGui.QListWidgetItem(i[1])
                self.direct_list.addItem(item)   
            
            # Create buttons for obtaining chat histories.
            group_btn = QtGui.QPushButton(
                                    "Get Group Chat History", self)
            group_btn.clicked.connect(self.get_group_history)
            direct_btn = QtGui.QPushButton(
                                    "Get Direct Message Chat History", self)
            direct_btn.clicked.connect(self.get_direct_history)
            
            # Show the labels, chat lists, and buttons.
            self.layout.addWidget(QtGui.QLabel(""))
            self.layout.addWidget(QtGui.QLabel("Select a Group Chat"))
            self.layout.addWidget(self.group_list)
            self.layout.addWidget(group_btn)
            self.layout.addWidget(QtGui.QLabel(""))
            self.layout.addWidget(QtGui.QLabel("Select a Direct Message Chat"))
            self.layout.addWidget(self.direct_list)
            self.layout.addWidget(direct_btn)
            
            self.list_exists = True
            
            self.setWindowTitle("Select a Chat to Retrieve History From")
    
    def get_group_history(self):
        """Retrieve group chat history."""
        group_id = self.groups[self.group_list.currentRow()][0]
        
        self.make_history(self.token_str, 'group', group_id)
    
    def get_direct_history(self):
        """Retrieve direct message chat history."""
        direct_id = self.directs[self.direct_list.currentRow()][0]
        
        self.make_history(self.token_str, 'direct', direct_id)
    
    def make_history(self, token, chat_type, chat_ID):
        """Create chat history file."""
        self.setWindowTitle("Retrieving Chat History, Please Wait...")
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

        # Obtain the user's ID to color the user's name in the chat file.
        self_id = get_self_id(token)

        f = open(('%s_chat_history.txt' % chat_ID), 'w')
        create_history(i_json, i_date, self_id, url, chat_type, f)
        f.close()
        format_history(chat_type, chat_ID) 
        
        self.setWindowTitle("Done")
    
    def cancel(self):
        """Close the window."""
        self.close()
            
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    
    aw = AppWindow()
    aw.setWindowTitle("Enter Your Access Token")
    aw.show()
    sys.exit(app.exec_())
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
