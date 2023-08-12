import pandas as pd
import os
from json import load
from sys import argv
from typing import Union, List

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def error(id: int = 0) -> None:
    global FILENAME
    ERROR_MESSAGE_ARGS = f"""
{Colors.FAIL}Error: Invalid argument(s).{Colors.ENDC}
{Colors.BOLD}Correct usage:{Colors.ENDC} python3 {FILENAME} <target_directory> <depth>
{Colors.BOLD}For more information, use:{Colors.ENDC} python3 loc.py help
    """
    if id == 0:
        print(ERROR_MESSAGE_ARGS)
    elif id == 1:
        print(f'{Colors.FAIL}Error: Invalid directory.{Colors.ENDC}')
    exit()
    
def help():
    global FILENAME
    HELP_MESSAGE =f"""
Correct usage: python3 {FILENAME} <target_directory> <depth>
{Colors.OKBLUE}target_directory:{Colors.ENDC} path to a folder to count lines of code in.
{Colors.OKBLUE}depth:{Colors.ENDC} non-negative integer or "all".
\tIf `depth` is "0" or "all", this script will search all subdirectories.
\tIf `depth` is a positive integer, this script will search up to subdirectories of that depth.
{Colors.BOLD}Example:{Colors.ENDC} python3 {FILENAME} '/Users/michael/Documents' all
    """
# {Colors.OKBLUE}file_types:{Colors.ENDC} list the file types to scan, separated by spaces.
# \tThis may be left blank.  If so, common file types will be searched.
# \tIncluding file types that do not contain code may cause errors.
    print(HELP_MESSAGE)
    exit()

def count_comments(lines: List[List[str]]) -> None:
    in_block_comment = False
    comment_count = 0

    for line in lines:
        line = line.strip()
        if not in_block_comment and line.startswith('#'):
            comment_count += 1
        elif line.startswith("'''") or line.startswith('"""'):
            comment_count += 1
            if not in_block_comment:
                in_block_comment = True
            else:
                in_block_comment = False
        elif in_block_comment:
            comment_count += 1

    return comment_count

def parse_ipy(extension: str, nb: str, file_df: pd.DataFrame) -> None:
    cells = load(open(nb))['cells']
    code_lines = [c['source'] for c in cells if c['cell_type'] == 'code']
    code_lines = [line for sublist in code_lines for line in sublist]
    md_lines = [c['source'] for c in cells if c['cell_type'] == 'markdown']
    md_lines = [line for sublist in md_lines for line in sublist]
    md_line_count = len(md_lines)
    num_lines = len(code_lines)
    num_comments = count_comments(code_lines)
    num_blanks = sum([(c.strip() == '') for c in code_lines])
    num_chars = sum(len(c) for c in code_lines) + sum(len(m) for m in md_lines)

    file_df.loc[file_df['file_extension'] == extension, 'file_count'] += 1
    file_df.loc[file_df['file_extension'] == extension, 'line_count'] += num_lines
    file_df.loc[file_df['file_extension'] == extension, 'comment_count'] += num_comments
    file_df.loc[file_df['file_extension'] == extension, 'blank_line_count'] += num_blanks
    file_df.loc[file_df['file_extension'] == extension, 'char_count'] += num_chars
    file_df.loc[file_df['file_extension'] == extension, 'markdown_line_count'] += md_line_count

def parse_nonipy(extension: str, filename: str, file_df: pd.DataFrame) -> None:
    with open(filename, 'r') as file:
        lines = file.readlines()
        num_lines = len(lines)
        num_comments = count_comments(lines)
        num_blanks = sum([(line.strip() == '') for line in lines])
        num_chars = sum([len(line) for line in lines])
    file_df.loc[file_df['file_extension'] == extension, 'file_count'] += 1
    file_df.loc[file_df['file_extension'] == extension, 'line_count'] += num_lines
    file_df.loc[file_df['file_extension'] == extension, 'comment_count'] += num_comments
    file_df.loc[file_df['file_extension'] == extension, 'blank_line_count'] += num_blanks
    file_df.loc[file_df['file_extension'] == extension, 'char_count'] += num_chars

def calc_lines(rootdir: str, maxdepth: Union[str, int], *args) ->  None:
    match rootdir:
        case str():
            try: os.listdir(rootdir)
            except: error(1)
        case _: error()
    match maxdepth:
        case int():
            if maxdepth < 0: error()
        case 'all': maxdepth = 0
        case _: error()
    VALID_FILETYPES = {
        '.c': 'C',
        '.h': 'C',
        '.java': 'Java',
        '.class': 'Java',
        '.py': 'Python',
        '.ipy': 'Python Notebook',
        '.ipython': 'Python Notebook',
        '.ipynb': 'Python Notebook',
        '.cs': 'cs',
        '.js': 'JavaScript',
        '.html': 'HTML',
        '.css': 'CSS'
    }
    if len(*args) > 0:
        for filetype in args:
            print(filetype)
            if filetype not in list(VALID_FILETYPES.keys()): error()
    
    file_df = pd.DataFrame({'file_extension': VALID_FILETYPES.keys(), 'language': VALID_FILETYPES.values()})
    file_df['file_count'] = 0
    file_df['line_count'] = 0
    file_df['comment_count'] = 0
    file_df['blank_line_count'] = 0
    file_df['markdown_line_count'] = 0
    file_df['char_count'] = 0
    
    for root, _, files in os.walk(rootdir):
        depth = root.count(os.path.sep) - rootdir.count(os.path.sep)
        if maxdepth != 0 and depth > maxdepth: break
        for file in files:
            for extension in VALID_FILETYPES.keys():
                if str(file).endswith(extension):
                    if extension in ['.ipynb', '.ipy', '.ipython']:
                        parse_ipy(extension=extension, nb=os.path.join(root, file), file_df=file_df)
                    else:
                        parse_nonipy(extension=extension, filename=os.path.join(root, file), file_df=file_df)
                    break
    print('',file_df)

if __name__ == '__main__':
    # run dir | target dir | depth | filetypes
    FILENAME = argv[0].split('/')[-1]
    if len(argv[1:]) <= 0: error()
    if argv[1] == 'help': help()
    if len(argv[1:]) <= 1: error()
    calc_lines(argv[1], argv[2], argv[3:])