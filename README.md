get_chat_history
=======

**'get_chat_history'** is an application that can retrieve and download the chat histories of a GroupMe user given that user's GroupMe Access Token. Three versions of the application exists:
* **get_chat_history.py** - interacts with the user via a windowed GUI. Run this script only if you have both Python and PyQt4.
* **get_chat_history_console.py** - interacts with the user via the command line or console. Run this script if you have Python but not PyQt4.
* **get_chat_history.exe** - an executable file that does what 'get_chat_history.py' does. Run this if you do not have Python or PyQt4. Obtain by downloading and extracting the .rar file in the '[executable](https://github.com/1Paint/groupme_chat_history/tree/master/executable)' folder. Download by pressing 'View Raw'.

Preview
-------
### Application
<img src="http://i.imgur.com/N0Zqphs.png">

<img src="http://i.imgur.com/5wgm16i.png">

<img src="http://i.imgur.com/YzT7iOv.png">
### Output
<img src="http://i.imgur.com/mV7iA3H.png">

Requirements
-------
* [Python 2.7.10+](https://www.python.org/downloads/)
* [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download) (not necessary if you are using 'get_chat_history_console.py')
* A GroupMe Access Token obtainable by logging in to [https://dev.groupme.com/](https://dev.groupme.com/) and clicking 'Access Token' at the top right.

If you are using the executable version, you do not need Python or PyQt4.

How To Use
-------
Download this repository via Git or by pressing the <a href="https://github.com/1Paint/GroupMe-Chat-History/archive/master.zip"><img src="http://i.imgur.com/RAFO5da.png button" align="top"></a> button.
Download the necessary requirements as indicated above. Run '.py' files with Python.

Please see '[app_manual.pdf](https://github.com/1Paint/groupme_chat_history/blob/master/documentation/app_manual.pdf)' in the '[documentation](https://github.com/1Paint/groupme_chat_history/tree/master/documentation)' folder on how to use the application.

If you are using the console version, run the script and follow the outputted instructions. If you are copying and pasting your Access Token and your Access Token does not appear, try right clicking the top of the window, selecting 'Edit', then pressing 'Paste'.

Possible Future Updates
-------
* A way to update existing chat history files. Not a top priority since this application is designed for one-time use.
* Distinguish users in the chat histories with more colors&mdash;not just green for the user and blue for everyone else.
