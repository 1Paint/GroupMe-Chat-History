"""This application retrieves the chat histories of a user when given
the user's access token.

Users can obtain access tokens at https://dev.groupme.com/ by logging
in and clicking 'Access Token' at the top right of the page.

Upon being given an access token, the application communicates with
GroupMe's public API (https://dev.groupme.com/docs/v3) and lists all
current group and direct message chats of the access token's owner.
The user can then select a chat and retrieve its history. The
application estimates the runtime upon retrieval.

Chat histories are retrieved with the most recent messages being
obtained first---Messages are thus written in reverse-chronological
order, top to bottom. These messages are put into a temporary text
file before being written in chronological order into an HTML file.
The temporary text file is then deleted and a CSS file is created
to format the HTML file for readability.
"""
import sys
import os
import time

import itertools
import re
import linecache
import urllib2
from json import load

from PyQt4 import QtGui, QtCore
    
message_limit = 100  # cannot be greater than 100.

def get_URL(token, chat_type, chat_ID, msg_ID):
    """Retrieve the API URL given an access token, chat type & ID, and optional
    message ID.
    """
    if chat_type == 'group':
        url = 'https://api.groupme.com/v3/groups/%s/messages' % chat_ID
        url += '?token=%s' % token
    elif chat_type == 'direct':
        url = 'https://api.groupme.com/v3/direct_messages'
        url += '?other_user_id=%s' % chat_ID
        url += '&token=%s' % token

    if msg_ID:
        url += '&before_id=%s' % msg_ID
    
    url += '&limit=%i' % message_limit

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

def create_history(json, url, self_id, chat_type, chat_ID,
                   msg_count, msg_limit, msg_ID):
    """Create a temporary chat history file.

    Retrieve and write down all dates, times, names, and messages in a
    GroupMe group chat. Messages are retrieved in reverse-chronological
    order---the most recent messages are retrieved first. The file is
    formatted in HTML and pairs with a corresponding CSS file.

    Parameters:
        json: The GroupMe API response in JSON format.
        url: The URL being worked with.
        self_id: The user's GroupMe ID.
        chat_type: The type of chat---'group' or 'direct'.
        chat_ID: The chat's ID.
        msg_count: The total number of messages in the chat.
        msg_limit: The number of messages retrieved in a set.
        msg_ID: Message ID needed to retrieve all earlier chat messages.
            Currently used only for repairing chat histories.
        
    Messages are written down one at a time, each time decrementing 'msg_count'
    by 1. When this count reaches 0, all messages have been retrieved.
    """
    if chat_type == 'group':
        msg = 'messages'
    elif chat_type == 'direct':
        msg = 'direct_messages'
        
    if msg_ID:
        f = open(('%s_chat_history_repair.txt' % chat_ID), 'w')
    else:
        f = open(('%s_chat_history.txt' % chat_ID), 'w')
    
    # Get the date of the most recent message. This date is needed as a
    # starting point to tell when the date next changes.
    initial_time = json['response'][msg][0]['created_at']
    old_date = time.strftime('%A, %d %B %Y', time.localtime(initial_time))
    
    # Record details of most recent message. Will be needed for updating chat
    # histories.
    after_id = json['response'][msg][0]['id']
    update_details = ('<p hidden update>%s %s %s %s</p>\n' 
                      % (chat_type, chat_ID, after_id, old_date))
    
    while msg_count > 0:
        # If there are less than 'msg_limit' messages to obtain, only
        # iterate through however many messages there are.
        if msg_count < msg_limit:
            msg_limit = msg_count % msg_limit
            
        for i in range(msg_limit):
            # Parse the data and retrieve times, names, and messages.
            # If the final number of messages is less than expected, set the
            # message count to 0 since all messages will have been retrieved.
            try:
                epoch_time = json['response'][msg][i]['created_at']
            except IndexError:
                msg_count = 0
                break
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

            # Once we have reached the 'msg_limit', store the latest message ID
            # and use it to obtain the API URL and JSON file for the next set
            # of messages. If there are no new messages, set the message count
            # to 0 to finish chat retrieval. Record HTTPErrors.
            msg_count -= 1
            if msg_count != 0 and i == msg_limit - 1:
                try:
                    before_id = json['response'][msg][i]['id']
                    new_url = '%s&before_id=%s' % (url, before_id)
                    json = get_json(new_url)
                except urllib2.HTTPError, err:
                    if err.code != 304:
                        f.write('<p hidden repair>%s %s %s %s</p>\n' 
                                % (chat_type, chat_ID, before_id, old_date))
                        f.write('<h1>ERROR: %s</h1>' % err.code)
                        f.write('<h1>msg: %s</h1>' % err.msg)
                        f.write('<h1>chat_type: %s</h1>' % chat_type)
                        f.write('<h1>chat_ID: %s</h1>' % chat_ID)
                        f.write('<h1>latest_message_id: %s</h1>\n' % before_id)
                    msg_count = 0

        if msg_count == 0:
            f.write(update_details)
            # Finally, write the group creation date.
            f.write('<tr><td class="date" colspan="3">%s</td></tr>\n' % old_date)
    
    f.close()

def format_history(chat_type, chat_ID, msg_ID):
    """Add HTML headers and footers and order messages from earliest to
    most recent, top to bottom. Reference the HTML file to a CSS file.
    """
    current_time = time.strftime("%Y%m%d-%H%M%S")
    
    if msg_ID:
        f = open('%s_chat_history_repair.txt' % chat_ID, 'r')
        final = open('%s_%s_chat_history_repair.html' % (chat_ID, chat_type), 'w')
    else:
        f = open('%s_chat_history.txt' % chat_ID, 'r')
        final = open('%s_%s_chat_history_%s.html' % (chat_ID, chat_type, current_time), 'w')

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
    if msg_ID:
        os.remove('%s_chat_history_repair.txt' % chat_ID)
    else:
        os.remove('%s_chat_history.txt' % chat_ID)

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

class AppWindow(QtGui.QDialog):
    """This is the main application window users interact with."""
    def __init__(self, msg_limit):
        QtGui.QDialog.__init__(self)
        self.msg_limit = msg_limit
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
        find_button.clicked.connect(self.list_chats)
        cancel_button = QtGui.QPushButton('Cancel')
        cancel_button.clicked.connect(self.close)

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(find_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(cancel_button, QtGui.QDialogButtonBox.ActionRole)

        button_line = QtGui.QHBoxLayout()
        button_line.addStretch(0)
        button_line.addWidget(button_box)
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

    def list_chats(self):
        """Find and list the chats available."""
        self.setWindowTitle("Loading...")

        token = str(self.token.text())  # obtain user-inputted token
        self.token_str = token.strip()
        valid = self.check_token(token)

        # Find all chats if the given token is valid.
        if valid == False:
            self.setWindowTitle("Please Check Your Access Token")
        elif valid == True:
            # Create the lists of group and direct message chats.
            if self.list_exists == False:
                self.group_list = QtGui.QListWidget()
                self.group_list.setFixedHeight(100)
                self.direct_list = QtGui.QListWidget()
                self.direct_list.setFixedHeight(100)
            # If lists already exist, clear them.
            else:
                self.group_list.clear()
                self.direct_list.clear()

            # Show the chat names.
            self.groups = get_groups(token)
            for i in self.groups:
                chat_name = QtGui.QListWidgetItem(i[1])
                self.group_list.addItem(chat_name)

            self.directs = get_directs(token)
            for i in self.directs:
                chat_name = QtGui.QListWidgetItem(i[1])
                self.direct_list.addItem(chat_name)

            # Highlight the first chat of each type.
            if self.group_list.count() > 0:
                self.group_list.item(0).setSelected(True)
            self.group_list.setFocus()

            if self.direct_list.count() > 0:
                self.direct_list.item(0).setSelected(True)
            self.direct_list.setFocus()
            
            # Create and show the interface if one doesn't already exist.
            if self.list_exists == False:
                # Create buttons for obtaining chat histories.
                self.group_btn = QtGui.QPushButton(
                    "Get Group Chat History", self)
                self.group_btn.clicked.connect(self.get_group_history)
                self.direct_btn = QtGui.QPushButton(
                    "Get Direct Message Chat History", self)
                self.direct_btn.clicked.connect(self.get_direct_history)

                # Initialize the status bar.
                self.status = QtGui.QStatusBar()
                self.status.setSizeGripEnabled(False)
                
                # Show the labels, chat lists, and get-history buttons.
                self.layout.addWidget(QtGui.QLabel(""))
                self.layout.addWidget(QtGui.QLabel("Select a Group Chat"))
                self.layout.addWidget(self.group_list)
                self.layout.addWidget(self.group_btn)
                self.layout.addWidget(QtGui.QLabel(""))
                self.layout.addWidget(QtGui.QLabel("Select a Direct Message Chat"))
                self.layout.addWidget(self.direct_list)
                self.layout.addWidget(self.direct_btn)
                self.layout.addWidget(QtGui.QLabel(""))
                
                # Create line for file selection (for repairing and updating).
                self.file_line = QtGui.QLineEdit()
                select_button = QtGui.QPushButton('Select Chat')
                select_button.clicked.connect(self.select_chat_file)

                select_line = QtGui.QHBoxLayout()
                select_line.addWidget(select_button)
                select_line.addWidget(self.file_line)
                
                # Show file selection line.
                self.layout.addLayout(select_line)
                
                # Create buttons for chat file repair and update.
                repair_button = QtGui.QPushButton('Repair')
                repair_button.clicked.connect(self.repair_history)
                update_button = QtGui.QPushButton('Update')
                update_button.clicked.connect(self.update_history)

                patch_box = QtGui.QDialogButtonBox()
                patch_box.addButton(repair_button, QtGui.QDialogButtonBox.ActionRole)
                patch_box.addButton(update_button, QtGui.QDialogButtonBox.ActionRole)

                patch_line = QtGui.QHBoxLayout()
                patch_line.addStretch(0)
                patch_line.addWidget(patch_box)
                patch_line.addStretch(0)
                
                # Show repair and update buttons.
                self.layout.addLayout(patch_line)
                self.layout.addWidget(QtGui.QLabel(""))
                self.layout.addWidget(self.status)
                
                self.list_exists = True

            self.setWindowTitle("Select a Chat to Retrieve History From")

    def get_group_history(self):
        """Retrieve group chat history."""
        group_id = self.groups[self.group_list.currentRow()][0]

        self.get_chat(self.token_str, 'group', group_id)

    def get_direct_history(self):
        """Retrieve direct message chat history."""
        direct_id = self.directs[self.direct_list.currentRow()][0]

        self.get_chat(self.token_str, 'direct', direct_id)

    def get_runtime(self, msg_count):
        """Estimate the time to retrieve the chat history based on the
        number of messages in the selected chat.
        """
        seconds = msg_count/360  # based on tests; 360 messages ~= 1 second
        minutes = seconds/60
        seconds = seconds % 60

        runtime = ("Estimated Runtime: %i minutes %i seconds"
            % (minutes, seconds))

        self.status.showMessage(runtime)

    def get_chat(self, token, chat_type, chat_ID, msg_ID=None):
        """Obtain the requested chat history and store it in a formatted
        HTML file with CSS.
        """
        # Obtain the relevant URL.
        url_general = get_URL(token, chat_type, chat_ID, None)
        url = get_URL(token, chat_type, chat_ID, msg_ID)

        # Obtain the most recent data set as a starting reference.
        try:
            i_json = get_json(url)
        except urllib2.HTTPError, err:
            self.status.showMessage("HTTP Error %s. Try again later." % err.code)
            return
            
        msg_count = i_json['response']['count']
        if msg_count == 0:
            self.status.showMessage("This chat does not contain any messages.")
        else:
            self.setWindowTitle("Retrieving Chat History, Please Wait...")
            
            # Estimate the runtime using the number of messages in the chat.
            self.get_runtime(msg_count)

            # Obtain the user's ID to color the user's name in the chat file.
            self_id = get_self_id(token)

            # Create the chat history file, format it into chronological order,
            # and create a corresponding CSS file.
            create_history(i_json, url_general, self_id, chat_type, chat_ID,
                           msg_count, self.msg_limit, msg_ID)
            format_history(chat_type, chat_ID, msg_ID)
            create_css()
            
            # Additional steps are needed if msg_ID is provided. A msg_ID is
            # provided when repairing/updating chat histories.
            if not msg_ID:
                self.status.showMessage("")
                self.setWindowTitle("Done")
    
    def select_chat_file(self):
        """Allow the user to select a file which is subsequently written to
        a line.
        """
        file = QtGui.QFileDialog.getOpenFileName(self, "Select chat history"
                                                 " file to repair or update")
        self.file_line.setText(file)
        
    def get_error_details(self, chat_name):
        """Given a chat history file name whose history was not fully 
        retrieved, return error details recorded when retrieval was prematurely
        terminated. These errors include the chat type and ID and message ID
        and its date. If no errors are found or if the file does not exist, the
        method returns None.
        """
        try:
            error_line = ""
            
            # Get the line in the chat containing error and chat details.
            file = open(chat_name)
            for i, line in enumerate(file):
                if i == 10: # Error details are recorded in line 11 of file.
                    error_line = line
                elif i > 10:
                    break
            file.close()
            error_details = re.search('<p hidden repair>(.*)</p>', error_line)
            return error_details
        except:
            return None
            
    def get_update_details(self, chat_name):
        """Given a chat history file name, return details of the most recent
        message. This includes the chat type and ID and the most recent message
        ID and its date."""
        try:
            update_line = ""
            
            # Get the line in the chat containing update and chat details.
            file = open(chat_name)
            for i, line in enumerate(file):
                if i == 8: # Update details are recorded in line 11 of file.
                    update_line = line
                elif i > 8:
                    break
            file.close()
            update_details = re.search('<p hidden update>(.*)</p>', update_line)
            return update_details
        except:
            return None
    
    def repair_history(self):
        """Repair a chat history file that had its chat retrieval prematurely
        terminated. 
        """
        chat_original = str(self.file_line.text())
        error_details = self.get_error_details(chat_original)
        
        try:
            chat_original = open(str(self.file_line.text()), 'r')
            if not error_details:
                self.status.showMessage("Are you sure the chat history file is"
                                        " valid?")
            else:
                error_details = error_details.group(1).split()
                chat_type = error_details[0]
                chat_ID = error_details[1]
                last_message_ID = error_details[2]
                earliest_date = error_details[3:]
                
                self.get_chat(self.token_str, chat_type, chat_ID, 
                              last_message_ID)
                
                chat_repair_name = ('%s_%s_chat_history_repair.html'
                                    % (chat_ID, chat_type))
                chat_repair = open(chat_repair_name, 'r')
                
                # Get the latest message date of the repair chat history file
                # and compare it to the earliest message date of original
                # history file. Needed to avoid writing the same date twice.
                update_details = self.get_update_details(chat_repair_name)
                update_details = update_details.group(1).split()
                latest_date = update_details[3:]
                if latest_date == earliest_date:
                    date_duplicate = True
                else:
                    date_duplicate = False
                
                self.merge(chat_ID, chat_type, chat_original, chat_repair, 
                           date_duplicate)
                self.status.showMessage("")
                self.setWindowTitle("Done")
        except IOError:
            self.status.showMessage("The file does not exist.")     
            
    def update_history(self):
        # To be written in the future.
        self.status.showMessage("Chat history updating will be added in the"
                                " future.")
        pass

    def merge(self, chat_ID, chat_type, chat_original, chat_repair, 
              date_duplicate):
        """Merge 2 chat histories together."""
        current_time = time.strftime("%Y%m%d-%H%M%S")
        chat_fixed = open('%s_%s_chat_history_%s.html'
                          % (chat_ID, chat_type, current_time), 'w')
        
        # Change usage of readlines(). High memory usage.
        chat_repair_lines = chat_repair.readlines()
        chat_original_lines = chat_original.readlines()
        
        # last 3 lines are HTML lines.
        chat_fixed.writelines(chat_repair_lines[:-3])
        
        # If the date of the latest 'repair messages' is not the same as the
        # date of the earliest 'original messages', make sure to distinguish
        # the dates of the those sets of messages.
        if not date_duplicate:
            chat_fixed.writelines(chat_original_lines[8])
            
        # chat messages start at line 12.
        chat_fixed.writelines(chat_original_lines[11:])
        
        chat_fixed.close()
        chat_original.close()
        chat_repair.close()

        os.remove(str(self.file_line.text()))
        os.remove('%s_%s_chat_history_repair.html' % (chat_ID, chat_type))
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    app_window = AppWindow(message_limit)
    app.setActiveWindow(app_window)
    
    app_window.setWindowTitle("Enter Your Access Token")
    app_window.move(0, 0)
    app_window.show()
    
    sys.exit(app.exec_())