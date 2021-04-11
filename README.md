
# GitHub Abuz

A python GUI app to blatantly abuz the git commit date feature to customize your GitHub Activity tiles thingy.

## Instructions

### Installing Dependencies

Assuming you've already installed [Python3](https://www.python.org/downloads/), run:

```bash
pip install -r requirements.txt
```

You also need to have [git](https://git-scm.com/downloads) set up on your local machine.

### Executing the Program

```bash
python qtAbuz.py
```

Once the UI loads, just enter your username and email ID and select the year you want your tile art to appear in.  
Then enter the link to the repository to which you want to spam the commits.  
**Note:** The link should be in `https://username:password@github.com/username/reponame` format, where username and password are those corresponding to your GitHub account.  
To create the tile art using the grid of checkboxes, the only real limit is your imagination (other than getting tired of clicking that is ;p)  
Using the text to matrix, however, as you'll soon realize, has many real limitations like the font sucking :'(  

### Notes

It should come as no surprise that `font.py` is stolen from [Dan Bader's blog](https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python) as 'black box' code that I don't understand yet (but I will :grin:)  
Other than that, it's just blankly staring at a lot of different documentations for hours :)  

"With great power comes great responsibility" - Ben Parker  
JK go wild! :joy:
