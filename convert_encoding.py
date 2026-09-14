import codecs
with open('project_structure.txt', 'r', encoding='utf-16le', errors='ignore') as f:
    content = f.read()
with open('project_structure_utf8.txt', 'w', encoding='utf-8') as f2:
    f2.write(content)
