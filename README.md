get_chat_history
=======

**'get_chat_history'** is an application that communicates with [GroupMe's API](https://dev.groupme.com/) and can retrieve and download the chat histories of a GroupMe user given that user's GroupMe Access Token. Three versions of the application exists:
* **get_chat_history.py** - interacts with the user via a windowed GUI. Run this script only if you have both Python and PyQt4.
* **get_chat_history_console.py (NO LONGER UP-TO-DATE)** - interacts with the user via the command line or console. Run this script if you have Python but not PyQt4.
* **get_chat_history.exe** - an executable file that does what 'get_chat_history.py' does. Run this if you do not have Python or PyQt4. Obtain by downloading and extracting the latest .rar file in the '[executable](https://github.com/1Paint/groupme_chat_history/tree/master/executable)' folder. Download by pressing 'View Raw'.

Update v1.1 (April 21, 2016)
-------
* A 'Repair' function now enables one to fix a chat history file whose chat retrieval was prematurely terminated due to an HTTP Error. Images shown below. Only works for chat histories obtained using v1.1+. The runtime listed when repairing chat histories is not accurate.
* The time of chat history retrieval is now added to the end of the chat history file name.
* Whitespace at the beginning and end of an inputted token are now ignored. Should fix the bugs people have been having with their tokens.
* Console version will now have lower/no priority in terms of updates.

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

Have Problems?
-------
Open up an issue in the 'Issues' tab at the top of the page.

To-do
-------
* Add function to update existing chat history files. Should work beginning with chat history files retrieved using v1.1+.
* Distinguish users in the chat histories with more colors&mdash;not just green for the user and blue for everyone else.
* Update application documentation (for repairing/updating).
* Refactor code and separate concerns so that create_history() and AppWindow's get_chat() don't need to take in so many parameters.
* Merge get_error_details() and get_update_details().
* Get accurate runtimes when repairing (and updating) chat histories.
* Find alternative to using 'readlines()' to avoid large memory usage.
* Possibly split extremely large files into separate files.
