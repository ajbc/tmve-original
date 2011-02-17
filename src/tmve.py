# external
import sys, os, shutil, codecs

# internal
from utils import *
from relations import *
from db import db

def parse_command():
    #TODO: expand command line arg options
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        messages.print_usage()
        sys.exit(2)
    
    args = sys.argv[1:]
    project_filename = ""

    for arg in args:
        if arg.startswith('-'):
            if arg == '--help' or arg == '-h':
                messages.print_help()
                sys.exit(0)
            elif arg == '--verbose' or arg == '-v':
                set_verbose(True)
            else:
                messages.print_unknown_option(sys.argv[1].lstrip('-'))
                sys.exit(2)
        else:
            project_filename = arg
            break

    return project_filename

def open_project(project_filename):
    try:
        project_file = open(project_filename)
    except IOError as (errnum, strerror):
        messages.print_file_read_error(project_filename, strerror)
        sys.exit(1)

    printv('Opened project file: \'' + project_filename + '\'')
    return project_file

def get_database_filename(project_file):
    line = project_file.readline()
    while (not line.strip().startswith(DATABASE_PREFIX)) and line != '':
        line = project_file.readline()
    
    if not line.startswith(DATABASE_PREFIX):
        messages.print_malformed_file('Project', project_file.name)
        sys.exit(1)
    
    database_filename = line[len(DATABASE_PREFIX):].strip()
    
    return database_filename

#string parsing helper function
def get_tokens_as_dict(line, prefix):
    token_dict = {}
    token_array = line[len(prefix):].split(',')
    for filename in token_array:
        if filename.strip() != '':
            token_dict[filename.strip()] = ''
    return token_dict

def get_template_requirements(template_name, template_file):
    html_strings = {}
    html_inserts = {}
    
    line_count = 1
    for line in template_file:
        line = line.strip()
        if line.startswith(COMMENT_BEGIN) or line == '':
            continue
        elif line.startswith(HTML_STRINGS_PREFIX):
            html_strings = get_tokens_as_dict(line, HTML_STRINGS_PREFIX)
        elif line.startswith(HTML_INSERTS_PREFIX):
            html_inserts = get_tokens_as_dict(line, HTML_INSERTS_PREFIX)
        else:
            messages.print_malformed_file("Template", template_name, "requirement", line_count, line.strip('\n'))
        line_count += 1
    
    return html_strings, html_inserts 

# determine template from project file
def get_template(project_file):
    template_line = ''
    while (template_line.strip() == '' or template_line.strip().startswith(COMMENT_BEGIN)):
        template_line = project_file.readline()
    if not template_line.startswith(TEMPLATE_PREFIX):
        messages.print_malformed_file('Project', project_file.name, 'template', 1, template_line.strip('\n'))
        sys.exit(1)

    template_name = template_line[len(TEMPLATE_PREFIX):].strip()
    template_filename = "src/templates/" + template_name + "/" + template_name + ".tmvt"
    
    try:
        template_file = open(template_filename)
    except IOError as (errnum, strerror):
        messages.print_file_read_error(template_filename, strerror)
        sys.exit(1)
        
    # import template module
    #TODO: need a try-except for non existing or bad py files
    #TODO: more extensive template validation 
    sys.path.append("src/templates/" + template_name)
    template = __import__(template_name)
    template.validate() #TODO: exit if this fails

    printv("Template " + template_name + " found and validated")
    
    return template_name, template_file

def fill_requirements(project_file, html_strings):
    # fetch required strings
    for line in project_file:
        #clean this up bigtime
        term = line.split(':', 1)[0]
        if html_strings.has_key(term):
            html_strings[term] = line.split(':', 1)[1].strip()
    
    for key in html_strings:
        if html_strings[key] == "":
            messages.print_warning("The HTML string \'" + key + "\' was not defined in the project file.")

    return html_strings

def create_project_dir(project_filename):
    # create project dir
    project_name = project_filename.split(".")[0]
    #case where project filename is project name
    if project_name == project_filename:
        project_name = project_name + "_dir"

    #TODO: consider not writing over the project dir and instead saving it elsewhere, or maybe give the option
    if os.path.isdir(project_name):
        shutil.rmtree(project_name)
        printv("Blowing away old project directory")
    os.makedirs(project_name)

    return project_name

def xml_rigamroll(src_filename, dst_filename, html_strings, html_inserts, template, myrelations, identifier):
    src_html_file = open(src_filename, 'r')
    dst_html_file = open(dst_filename, 'w')
    printv("  " + dst_filename)

    # insert strings into html file
    for line in src_html_file:
        line = line.replace("<tmv-css>", "styling.css")
        for key in html_strings:
            xml_key = "<tmv-" + key + ">"
            line = line.replace(xml_key, html_strings[key])
        for key in html_inserts: #TODO: html_inserts should be array not dict
            xml_key = "<tmv-" + key + ">"
            if line.find(xml_key) != -1:
                line = line.replace(xml_key, template.get_html_insert(key, myrelations, identifier))
        dst_html_file.write(line)

def build_ajax(project_name, template_name, html_strings, html_inserts, myrelations):
    # copy css files 
    #TODO: consider moving css files to a css dir
    shutil.copy("src/templates/" + template_name + "/" + template_name + ".css", project_name + "/styling.css")

    # import template-specific source
    sys.path.append("src/templates/" + template_name)
    template = __import__(template_name)

    # copy template html files to project dir
    html_dir = "src/templates/" + template_name + "/html/"
    html_filenames = os.listdir(html_dir)
    for html_filename in html_filenames:
        if html_filename.startswith('.'):
            continue
        src_filepath = html_dir + html_filename
        dst_filepath = project_name + "/" + html_filename

        if html_filename.endswith(".html"):
            xml_rigamroll(src_filepath, dst_filepath, html_strings, html_inserts, template, myrelations, None)
        elif os.path.isdir(html_dir + html_filename):
            printv("Directory: "+ html_filename)
            if html_filename == "images" or html_filename == "js":
                shutil.copytree("src/templates/" + template_name + "/html/" + html_filename, project_name + "/" + html_filename + "/")
                continue
            
            os.makedirs(dst_filepath)

            tokenset = []
            tokentype = ''
            
            if html_filename == "browse":
                for filename in os.listdir(html_dir + html_filename):
                    if filename.startswith('.'):
                        continue
                    src = src_filepath + '/' + filename
                    dst = dst_filepath + '/' + filename
                    xml_rigamroll(src, dst, html_strings, html_inserts, template, myrelations, None)
                continue
            elif html_filename == "topics":
                token_type = "topic"
                tokenset = relations.get_topics(myrelations)
            elif html_filename == "docs":
                token_type = "doc"
                tokenset = relations.get_docs(myrelations)
            elif html_filename == "terms":
                token_type = "term"
                tokenset = relations.get_terms(myrelations)
            else:
                printv("not sure what to do...")

            #TODO: expand to find multiple html files per dir
            src_filename = ''
            filenames = os.listdir(html_dir + html_filename)
            i = 0
            while src_filename == '' or src_filename.startswith('.'):
                src_filename = filenames[i] # find the one html file here
                i += 1
            src_filepath += "/" + src_filename
            printv(" source file: " + src_filepath)

            for token in tokenset:
                token_dst_filepath =  dst_filepath + "/" + token.get_safe_title() + ".html"
                token_html_strings = html_strings.copy()
                token_html_strings[token_type] = token.title #token-specific
                xml_rigamroll(src_filepath, token_dst_filepath, token_html_strings, html_inserts, template, myrelations, token)

def main():
    project_filename = parse_command()
    project_file = open_project(project_filename)
    template_name, template_file = get_template(project_file)
    import_template(template_name)
    database_filename = get_database_filename(project_file)
    html_strings, html_inserts = get_template_requirements(template_name, template_file)
    html_strings = fill_requirements(project_file, html_strings)
    
    project_name = create_project_dir(project_filename)
    
    # open sqlite relational database
    printv("Using database: " + database_filename)
    myrelations = relations(db(database_filename))

    build_ajax(project_name, template_name, html_strings, html_inserts, myrelations)     
    
if __name__ == "__main__":
    main()
