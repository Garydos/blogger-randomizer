# blogger-randomizer
A randomizer for google blogger blogs (aka blogspot.com blogs)

### Prerequisites
Python 3 installed and available on the command line

### Installing
Move the "blogger randomizer" directory to a location of your choosing and add it to your $PATH environment variable for easy access to the script

### Usage
Place the url's for blogs you'd like to randomize in the blogs.txt file, with each blog in its own line

Example blogs.txt:
```
http://afrofunkforum.blogspot.com/
http://funkatropolis.blogspot.com/
http://bristolfunk.blogspot.com/
```

To run the script, simply call it from the command line

For example:
```
./bloggerapi.py
```

If you are running it from the blogger randomizer directory

### Notes
This script will cache the contents of each blog onto your harddrive in .pcle and .lastupdate files.  Do not move the .py script out of its blogger randomizer directory in order to avoid messying up other directories
