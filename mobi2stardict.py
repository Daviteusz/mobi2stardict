#!/usr/bin/env python3

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from lxml import etree as ET
from lxml import html

import argparse
import glob
import re
import os
import sys

@dataclass
class Entry:
    HW: str
    INFL: set[str]
    BODY: str

@dataclass
class Metadata:
    Title: str
    Description: str
    Creator: str
    Date: str
    InLang: str
    OutLang: str

def soup_gettext(_find) -> str:
    return _find.text.strip() if _find else ""

def get_metadata(path: str) -> Metadata:
    _base_dir = str(Path(path).parent.absolute().resolve())
    opf_file = glob.glob(os.path.join(_base_dir, "*.opf"))

    if not opf_file:
        print("No OPF file found in the specified folder.")
        return Metadata("", "", "", "", "", "")

    opf_path = opf_file[0]

    try:
        with open(opf_path, "r", encoding="utf-8") as f:
            opf_soup = BeautifulSoup(f.read(), "lxml-xml")
    except:
        print("Could not read opf file.")
        return Metadata("", "", "", "", "", "")

    title_tag = opf_soup.find("dc:title")
    title = soup_gettext(title_tag) if title_tag else ""

    return Metadata(
        Title=soup_gettext(opf_soup.find("dc:Title")),
        Description=soup_gettext(opf_soup.find("dc:description")),
        Creator=soup_gettext(opf_soup.find("dc:creator")),
        Date=soup_gettext(opf_soup.find("dc:date")),
        InLang=soup_gettext(opf_soup.find("DictionaryInLanguage")),
        OutLang=soup_gettext(opf_soup.find("DictionaryOutLanguage"))
    )

def set_metadata(_key: str, _metadata: Metadata, dict_name: str, author: str):
    if _key == 'Title':
        _title = dict_name if dict_name else _metadata.Title
        if dict_name and _metadata.InLang:
            _title += f" ({_metadata.InLang.replace('-', '_')}"
        if dict_name and _metadata.OutLang:
            _title += f"-{_metadata.OutLang.replace('-', '_')}"
        if dict_name and (_metadata.InLang or _metadata.OutLang):
            _title += ")"
        return _title if _metadata.Title else dict_name
    if _key == 'Desc':
        return _metadata.Description
    if _key == 'Creator':
        return _metadata.Creator if _metadata.Creator else author
    if _key == 'Date':
        return _metadata.Date if _metadata.Date else datetime.today().strftime('%d/%m/%Y')


def fix_links(body_str: str) -> str:
    temp = BeautifulSoup(body_str, "lxml")
    for link in temp.find_all("a", href=True):
        body_str = re.sub(link["href"], f"bword://{link.getText()}", body_str)
    return body_str

def process_entry(entry, fix_links):
    headword = entry.find("idx:orth").get("value")
    inflections = entry.find("idx:infl")
    inflections_set = {i.get("value") for i in inflections.find_all("idx:iform")} if inflections else None

    body_re = re.search("<\/idx:orth>(.*?)<\/idx:entry>", str(entry), re.S)
    body = body_re.group(1) if body_re else ""

    if not body:
        body = "".join([str(t) for t in entry.next_siblings if t.name not in ("idx:entry", "mbp:pagebreak")])

    if not body:
        return None

    if fix_links:
        body = fix_links(body)

    temp = BeautifulSoup(body, "lxml")
    temp = process_html_body(temp)

    if inflections_set:
        inflections_set.discard(headword)
        return Entry(headword, inflections_set, str(temp))
    else:
        return Entry(headword, set(), str(temp))

def process_html_body(temp):
    first_heading = temp.find("h1")
    if first_heading:
        first_heading.decompose()

# Enable this if you want some style formatting (not recommended method)
# You should create .css file next to the .ifo file (recommended)
# CSS styles can be found in HTML files.
    
 #   for div in temp.find_all("div"):
  #      div.attrs['style'] = 'text-align:left; margin-left:1em;'
#
 #   for i in range(1, 7):  # For headings h1 to h7
  #      for heading in temp.find_all(f"h{i}"):
   #         heading.attrs['style'] = 'margin-left:-1em;'
#
 #   for paragraph in temp.find_all("p", {"class": "s"}):
  #      paragraph.attrs['style'] = 'text-align:right; font-style:italic; font-size:80%;'
#
 #   for span in temp.find_all("span", {"class": "m"}):
  #      span.attrs['style'] = 'font-weight:bold;'

    return temp.div

def convert(folder_path: str, dict_name: str, author: str, fix_links: bool, gls: bool, textual: bool, chunked: bool) -> None:
    html_files = sorted(Path(folder_path).glob("*.html"))
    if not html_files:
        sys.exit("No HTML files found in the specified folder.")

    arr = []
    cnt = 0
    for idx, html in enumerate(html_files, start=1):
        try:
            with open(html, "r", encoding="utf-8") as f:
                book = f.read()
        except FileNotFoundError:
            sys.exit(f"Could not open the file: {html}. Check the filename.")

        if "<idx:" not in book:
            sys.exit("Not a dictionary file.")

        entry_groups = []
        if chunked:
            cnt = 0
            temp = []
            parts = book.split("<idx:entry")[1:]
            last_part = parts[-1]
            for p in parts:
                if p:
                    temp.append(("<idx:entry" + p))
                    cnt += 1
                    if cnt == 5000 or p == last_part:
                        entry_groups.append("".join(temp))
                        cnt = 0
                        temp = []
        else:
            entry_groups.append(book)

        for group in entry_groups:
            soup = BeautifulSoup(group, "lxml")
            entries = soup.find_all("idx:entry")
            for entry in entries:
                entry_result = process_entry(entry, fix_links)
                if entry_result:
                    arr.append(entry_result)
                    cnt += 1
                    print(f"> Processing file {idx}/{len(html_files)}: {html} - Parsed {cnt:,} entries.", end="\r")

    print()

    meta = get_metadata(path=str(html_files[0]))  # Assuming metadata is the same for all files

    if gls:
        create_gls_file(arr, dict_name, author, meta)

    if textual:
        create_textual_xml(arr, meta, dict_name, author)

def create_gls_file(arr, dict_name, author, meta):
    gls_metadata = f"\n#stripmethod=keep\n#sametypesequence=h\n"
    gls_metadata += f"#bookname={set_metadata('Title', meta, dict_name, author)}\n"
    gls_metadata += f"#author={set_metadata('Creator', meta, dict_name, author)}\n\n"
    with open("book.gls", "w", encoding="utf-8") as d:
        d.write(gls_metadata)
        for entry in arr:
            headwords = f"{entry.HW}|{'|'.join(entry.INFL)}" if entry.INFL else entry.HW
            single_def = f"{headwords}\n{entry.BODY}\n\n"
            d.write(single_def)
            d.flush()

def create_textual_xml(arr, meta, dict_name, author):
    root = ET.Element("stardict")

    info = ET.SubElement(root, "info")
    version = ET.SubElement(info, "version").text = "3.0.0"
    bookname = ET.SubElement(info, "bookname").text = set_metadata('Title', meta, dict_name, author)
    author_ = ET.SubElement(info, "author").text = set_metadata('Creator', meta, dict_name, author)
    desc = ET.SubElement(info, "description").text = set_metadata('Desc', meta, dict_name, author)
    email = ET.SubElement(info, "email").text = ""
    website = ET.SubElement(info, "website").text = ""
    date = ET.SubElement(info, "date").text = set_metadata('Date', meta, dict_name, author)
    dicttype = ET.SubElement(info, "dicttype").text = ""

    for entry in arr:
        article = ET.SubElement(root, "article")
        key = ET.SubElement(article, "key").text = entry.HW
        for i in entry.INFL:
            syn = ET.SubElement(article, "synonym").text = i
        cdata = ET.CDATA(entry.BODY)
        defi = ET.SubElement(article, "definition")
        defi.attrib["type"] = "h"
        defi.text = cdata

    xml_str = ET.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
    with open("book_stardict_textual.xml", "wb") as d:
        d.write(xml_str)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert unpacked Kindle MOBI dictionary files to Babylon Glossary source files or to Stardict Textual Dictionary Format.")
    parser.add_argument('--html-folder', default='.', help="Path of the folder containing HTML files.")
    parser.add_argument('--fix-links', action='store_true', help="Try to convert in-dictionary references to glossary format.")
    parser.add_argument('--dict-name', default=None, help="Name of the dictionary file.")
    parser.add_argument('--author', default="author", help="Name of the author or publisher.")
    parser.add_argument('--gls', action='store_true', help="Convert dictionary to Babylon glossary source.")
    parser.add_argument('--textual', action='store_true', help="Convert dictionary to Stardict Textual Dictionary Format.")
    parser.add_argument('--chunked', action='store_true', help="Parse html in chunks to reduce memory usage.")
    args = parser.parse_args()

    if not (args.gls or args.textual):
        sys.exit("You need to specify at least 1 output format: --gls, --textual, or both.")

    html_files = sorted(Path(args.html_folder).glob("*.html"))
    if not html_files:
        sys.exit("No HTML files found in the specified folder.")

    meta = get_metadata(path=str(html_files[0]))  # Assuming metadata is the same for all files

    dict_name = args.dict_name if args.dict_name else set_metadata('Title', meta, None, None)

    convert(args.html_folder, dict_name, args.author, args.fix_links, args.gls, args.textual, args.chunked)
