# mobi2stardict
Convert unpacked MOBI dictionaries to StarDict input formats: Babylon Glossary Source (GLS) format and StarDict Textual Dictionary Format

# Usage
`python mobi2stardict.py -h`
```
usage: mobi2stardict.py [-h] [--html-folder HTML_FOLDER] [--fix-links] [--dict-name DICT_NAME] [--author AUTHOR] [--gls]
                        [--textual] [--chunked]

Convert unpacked Kindle MOBI dictionary files to Babylon Glossary source files or to Stardict Textual Dictionary Format.

options:
  -h, --help            show this help message and exit
  --html-folder HTML_FOLDER
                        Path of the folder containing HTML files.
  --fix-links           Try to convert in-dictionary references to glossary format.
  --dict-name DICT_NAME
                        Name of the dictionary file.
  --author AUTHOR       Name of the author or publisher.
  --gls                 Convert dictionary to Babylon glossary source.
  --textual             Convert dictionary to Stardict Textual Dictionary Format.
  --chunked             Parse html in chunks to reduce memory usage.
```
You need to install [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup) and [lxml](https://lxml.de/installation.html) packages to run the script.
To convert the unpacked MOBI files to both GLS and Textual format you would call the script like this:
````
python mobi2stardict.py --fix-links --html-folder ./Folder --dict-name "Name of the dictionary" --author "Author" --gls --textual
````
Change name and author accordingly or not specify these parameters.

Also, while converting particularly large files you may want to pass the `--chunked` option to bring down the memory usage to more moderate levels. Then the line would become:
````
python.exe mobi2stardict.py --fix-links --dict-name "Name of the dictionary" --author "Author" --gls --textual --chunked
````

# NOTE
You may come across some poorly formatted dictionaries that may result in inability to parse definitions.
