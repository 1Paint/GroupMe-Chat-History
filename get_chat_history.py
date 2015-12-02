import sys
import os
import time

from urllib2 import urlopen
from json import load

from PyQt4 import QtGui, QtCore

message_limit = 100  # cannot be greater than 100

def get_URL(token, group_id):
    url = "https://api.groupme.com/v3/groups/%s/messages" % group_id
    url += "?token=%s" % token
    url += "&limit=%i" % message_limit
    
    return url

def get_json(url):
    """Obtain information in JSON format."""
    response = urlopen(url)
    json_obj = load(response)
        
    return json_obj

def get_chat_history(json, old_date, url, f):
    """
    Retrieve and write down all dates, times, names, and messages in a
    groupme group chat. Messages are retrieved in reverse-chronological
    order---the most recent messages are retrieved first.

    Parameters:
        json: The GroupMe API response in JSON format.
        old_date: The date of the most recent message.
        url: The URL being worked with.
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
    try:
        for i in range(message_limit):
            
            # Parse the data and retrieve times, names, and messages.
            epoch_time = json['response']['messages'][i]['created_at']
            date = time.strftime('%d %b %Y', time.localtime(epoch_time))
            hour = time.strftime('%H:%M:%S', time.localtime(epoch_time))

            name = json['response']['messages'][i]['name']
            text = json['response']['messages'][i]['text']
            line = '%s %s: %s\n' % (hour, name, text)

            # Separate messages by date.
            if date != old_date:
                f.write('=======\n%s\n\n' % old_date)
                old_date = date

            # Write times, names, and messages.
            f.write(line.encode('ascii', 'ignore'))

            # Iterate through the next set of messages.
            if i == message_limit-1:
                before_id = json['response']['messages'][i]['id']
                next_url = "%s&before_id=%s" % (url, before_id)
                next_json_obj = get_json(next_url)
                get_chat_history(next_json_obj, old_date, url, f)
                
    except IndexError:
        f.write('=======\n%s\n' % old_date)  # date of group creation

def reverse(group_id):
    """Order messages from earliest to most recent, top to bottom."""
    f = open(('%s_history.txt' % group_id), 'r')
    final = open(('%s_chat_history.md' % group_id), 'w')

    # Correctly order the messages.
    for line in reversed(f.readlines()):
        final.write(line)

    f.close()
    final.close()
    os.remove('%s_history.txt' % group_id)  # delete reversed-chat file

class AppWindow(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setFixedSize(350, 110)
        
        layout = QtGui.QGridLayout()

        token_label = QtGui.QLabel("Access Token")
        self.token = QtGui.QLineEdit()
        self.token.setFixedWidth(250)
        token_line = QtGui.QHBoxLayout()
        token_line.addStretch(0)
        token_line.addWidget(token_label)
        token_line.addWidget(self.token)
        
        group_id_label = QtGui.QLabel("Group ID")
        self.group_id = QtGui.QLineEdit()
        self.group_id.setFixedWidth(250)
        group_id_line = QtGui.QHBoxLayout()
        group_id_line.addStretch(0)
        group_id_line.addWidget(group_id_label)
        group_id_line.addWidget(self.group_id)
        
        update_button = QtGui.QPushButton('Ok')
        update_button.clicked.connect(self.okay)
        cancel_button = QtGui.QPushButton('Cancel')
        cancel_button.clicked.connect(self.cancel)
        
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton(update_button, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(cancel_button, QtGui.QDialogButtonBox.ActionRole)
        
        button_line = QtGui.QHBoxLayout()
        button_line.addStretch(0)
        button_line.addWidget(buttonBox)
        button_line.addStretch(0)
                
        layout.addLayout(token_line, 0, 0)
        layout.addLayout(group_id_line, 1, 0)
        layout.addLayout(button_line, 2, 0)
        
        self.setLayout(layout)

    # Obtain the chat log.
    def okay(self):
        self.setWindowTitle("Please Wait")
        
        token = str(self.token.text())
        group_id = str(self.group_id.text())
        
        url = get_URL(token, group_id)
        
        initial_json = get_json(url)
        initial_time = initial_json['response']['messages'][0]['created_at']
        initial_date = time.strftime('%d %b %Y', time.localtime(initial_time))
        
        f = open(('%s_history.txt' % group_id), 'w')
        get_chat_history(initial_json, initial_date, url, f)
        f.close()
        reverse(group_id)
        
        self.setWindowTitle("Done")
        
    # Close the window.
    def cancel(self):
        self.close()
            
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    
    aw = AppWindow()
    aw.setWindowTitle("Get GroupMe Group Chat History")
    aw.show()
    sys.exit(app.exec_())
