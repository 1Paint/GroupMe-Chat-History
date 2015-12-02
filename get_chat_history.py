import sys
import os
import time

from urllib2 import urlopen
from json import load

from PyQt4 import QtGui, QtCore

message_limit = 100  # cannot be greater than 100

def get_URL(token, group_id):
    """Retrieve the URL given an access token and group ID."""
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

            name = json['response']['messages'][i]['name']
            hour = time.strftime('%H:%M:%S', time.localtime(epoch_time))
            text = json['response']['messages'][i]['text']
            if text: text = text.encode('unicode-escape')  # escape \n, etc.

            # format into HTML
            name = '<td nowrap align="right" valign="top"><b>%s' % name
            hour = '(%s):</b></td>' % hour
            text = '<td>%s</td>' % text
            line = '<tr>%s %s %s</tr>\n' % (name, hour, text)

            # Separate messages by date.
            if date != old_date:
                f.write('<table>\n')
                f.write('<tr><td><h3>%s</h3></td></tr>\n' % old_date)
                f.write('</table>\n')
                old_date = date

            # Write times, names, and messages.
            f.write(line.encode('UTF-8', 'replace'))

            # Iterate through the next set of messages.
            if i == message_limit-1:
                before_id = json['response']['messages'][i]['id']
                next_url = "%s&before_id=%s" % (url, before_id)
                next_json_obj = get_json(next_url)
                get_chat_history(next_json_obj, old_date, url, f)
                
    except IndexError:
        f.write('<table>\n')
        f.write('<tr><h3>%s</h3></tr>\n' % old_date)  # date of group creation

def final_format(group_id):
    """
    Add HTML headers and footers and order messages from earliest to
    most recent, top to bottom.
    """
    f = open(('%s_history.txt' % group_id), 'r')
    final = open(('%s_chat_history.html' % group_id), 'w')

    header = '<!DOCTYPE html>\n<html>\n<body>\n'
    final.write(header)

    # Correctly order the messages.
    for line in reversed(f.readlines()):
        final.write(line)

    footer = '</body>\n</html>'
    final.write(footer)

    f.close()
    final.close()
    os.remove('%s_history.txt' % group_id)  # delete reverse-chronological chat file

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

    def okay(self):
        """Obtain and format the chat log."""        
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
        final_format(group_id)
        
        self.setWindowTitle("Done")
        
    def cancel(self):
        """Close the window."""
        self.close()
            
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    
    aw = AppWindow()
    aw.setWindowTitle("Get GroupMe Group Chat History")
    aw.show()
    sys.exit(app.exec_())
