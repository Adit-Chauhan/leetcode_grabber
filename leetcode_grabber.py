#!/usr/bin/env python3

import os
import sys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from bs4.element import Tag,NavigableString
import argparse

IDENT = "    "

class Example:
    inp = ""
    out = ""
    explain = ""

    def __init__(self,pre:Tag|NavigableString)->None:
        lines = pre.text.splitlines()
        self.inp = lines[0].replace("Input:","").strip()
        self.out = lines[1].replace("Output:","").strip()
        if self.out == "true" or self.out == "false":
            self.out = self.out.capitalize()
        try:
            self.explain = lines[2].strip()
        except IndexError:
            self.explain = "No explaination"

class Question:
    title = ""
    number = 0
    rating = ""
    description = ""
    examples = []
    starter = []
    function_name = ""
    def __init__(self,html) -> None:
        print("Parsing Source Code")
        html = BeautifulSoup(html,"html.parser")

        print("Collecting Title")
        if (div := html.find("div",{"data-cy":"question-title"})) is not None:
            self.get_title_and_number(div)
        else:
            print("Failed to parse Title or Number")
            sys.exit(1)

        if (div := html.find("div",{"class":"css-10o4wqw"})) is not None:
            self.get_difficulty(div)
        else:
            print("Failed to parse difficulty")
            sys.exit(1)

        if (div:= html.find("div",{"class":"content__u3I1 question-content__JfgR"})) is not None:
            print("Collecting Description")
            self.get_description(div)
            print("Collecting examples")
            self.examples = [Example(p) for p in div.findAll("pre")]
        else:
            print("Failed to parse Description")
            sys.exit(1)

        if (div:= html.find("div",{"class":"CodeMirror-lines"})) is not None:
            self.get_starter(div)
        else:
            print("Failed to parse Starter code")
            sys.exit(1)


    def get_starter(self,div:Tag|NavigableString):
        self.starter = [x.text.strip() for x in div.find("div",{"class":"CodeMirror-code"}).findAll("pre")]

    def get_title_and_number(self,div:Tag|NavigableString):
        title = div.text
        titles = title.split('.')
        self.number = int(titles[0])
        self.title = titles[1].strip()

    def get_difficulty(self,div:Tag|NavigableString):
        divs = div.find("div")
        self.rating = divs.text

    def get_description(self,div:Tag|NavigableString):
        inner = div.find("div")
        paras = inner.findAll("p")
        description = ""
        for p in paras:
            if p.text == "Example 1:":
                break
            description = description + p.text + '\n'

        self.description =description.strip()

    def print_starter_code(self) -> str:
        i = 0
        while "class Solution" not in self.starter[i]:
            i += 1
        F = "\n".join(self.starter[:i])

        sep = f"\n{IDENT}".join(self.starter[i:])
        return f"{F}\n{sep}"

    def solution_file_str(self) -> str:
        des = "#" + "\n\n#".join(self.description.splitlines())
        return f"{des}\n\nfrom typing import *\n\n{self.print_starter_code()}"


    def function(self):
        i = 0
        while "class Solution" not in self.starter[i]:
            i += 1
        string = self.starter[i+1]
        string = string.replace("def","").strip()
        string = string.replace("self, ","")
        return string

    def filename(self)->str:
        return f"{self.rating[0]}_{self.number}_{self.title.replace(' ','_')}.py"

    def append_test(self):
        testFile = ""
        match self.rating:
            case "Easy": testFile = "test_easy.py"
            case "Medium": testFile = "test_medium.py"
            case "Hard": testFile = "test_hard.py"
            case other: testFile = "test_hard.py"

        with open(testFile,"a") as fp:
            func = self.function()
            lines = [f"\n\ndef test_{func[:func.find('(')]}():",f"from {self.filename()[:-3]} import Solution","sol = Solution()"]
            for example in self.examples:
                lines.extend([f"assert sol.{func[:func.find('(')+1]}{example.inp}) == {example.out}",f"#{example.explain}"])
            fp.write(f"\n{IDENT}".join(lines))

    def make_file(self):
        with open(self.filename(),"w") as fp:
            fp.write(self.solution_file_str())


def init_files():
    def make_file(fname):
        if not os.path.exists(fname):
            with open(fname,"w") as fp:
                fp.write("#!/usr/bin/env python3\n")
    make_file("test_easy.py")
    make_file("test_medium.py")
    make_file("test_hard.py")


if __name__ == "__main__":
    # Init and Argument parsing
    init_files()
    parser = argparse.ArgumentParser()
    parser.add_argument("url",help="Url to parse")
    parser.add_argument("--head",help="See the browser",action="store_true")
    args=  parser.parse_args()
    if args.head:
        dr = Firefox()
    else:
        op = Options()
        op.headless = True
        dr = Firefox(options=op)

    try:
        print("Connecting to url")
        dr.get(args.url)

        element = WebDriverWait(dr,20).until(EC.invisibility_of_element_located((By.ID,"initial-loading")))
        print("changing source to python")
        dr.find_element(By.CLASS_NAME,"ant-select-selection__rendered").click()
        WebDriverWait(dr,20).until(EC.visibility_of_element_located((By.XPATH,"//li[text()='Python3']"))).click()
        html = dr.page_source
        dr.close()
    except Exception as e:
        print(e)
        dr.close()
        sys.exit(1)
    q = Question(html)
    print("making Starter File")
    q.make_file()
    print("Adding tests")
    q.append_test()
    os.remove("geckodriver.log")
