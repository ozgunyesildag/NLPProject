import docx2txt

def convertDocxToText(path):
    document = docx2txt.process(path)
    return document