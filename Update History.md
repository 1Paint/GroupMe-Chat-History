(April 22, 2016)
-------
* Fixed repair function in executable version. py2exe .exe files do not correctly run linecache.getline(). Instead, use for-loop and enumerate() to get needed file line.
* Fixed repair function bug where no new JSON files were being obtained. The URL being passed for chat retrieval contained an unchanging before_id. Now uses the general URL without any message IDs.

(April 21, 2016)
-------
* Update to v1.1
* A 'Repair' function now enables one to fix a chat history file whose chat retrieval was prematurely terminated due to an HTTP Error. Only works for chat histories obtained using v1.1+. The runtime listed when repairing chat histories is not accurate.
* The time of chat history retrieval is now added to the end of the chat history file name.
* Whitespace at the beginning and end of an inputted token are now ignored. Should fix the bugs people have been having with their tokens.
* Console version will now have lower/no priority in terms of updates.
