import re
import json
import glob
import pandas
import spacy
import spacy.matcher
from PDFtoText import convertPDFToText
from DOCXtoText import convertDocxToText

nlp = spacy.load("en_core_web_sm")


def getContent(filename):
    extension = filename.split(".")[-1]
    if extension == "txt":
        f = open(filename, "r")

        content = f.readlines()

        f.close()
    elif extension == "docx":

        content = convertDocxToText(filename)

    elif extension == "pdf":

        content = convertPDFToText(filename)

    return content


def getAllPaths():
    paths = glob.glob('docx/*docx')

    return paths


def getExpertiseLevel(cont, data):
    level = ["senior", "junior"]  # level array
    exp = []
    for line in cont.splitlines():
        for key in level:  # keylerde dolaşıyorum
            if key in line.lower():  # bulursam
                exp.append(key)  # ekliyorum
    pattern = re.compile(r'(.*[Yy]ear[s].*)')  # ayrıca bu regexte yearı arayıp buluyorum
    matches = pattern.findall(cont)
    matches = list(matches)
    for match in matches:  # buldugum year linelarda dolaşıp
        if match:
            match = match.replace(u'\xa0', u' ')
            exp.append(match)  # varsa onu da ekliyorum

    exp = list(set(exp))

    data['expertiseLevel'] = exp


def getLanguageLine(cont, data):
    language = ["english", "german", "french", "arabic"]  # dil listesi
    temp = []

    for line in cont.splitlines():
        for key in language:
            if key in line.lower():  # varsa
                doc = nlp(line)
                for token in doc.noun_chunks:  # isim tamlamalarında dolaşıp
                    if key in token.text.lower():  # buldugum tamlamaları ekliyorum
                        temp.append(token.text)
    temp = list(set(temp))
    data['foreignLanguage'] = temp


    return temp, data


def getSkillLine(cont):
    keywords = ["framework", "query ", "apache cassandra", "spring boot", "spark", "jupyter",
                "sql", "technology", "api", "git", "svn", "linux", "bash", "jira", "confluence",
                "mongo", "redi", "html", "qliksense", "node.js",
                "qlikview", "angular", " react ", "sap", "pmp",
                "sirsid", "object or", "object-or", " oop ",
                " ebs ", " sqs ", " route53", "cloud", "opswork", "flink",
                "elastic ", "websockets", "agile", "azure", "vsts", "java", "jmp", " r ", " r,",
                "swagger", "b2b", "b2c", "tableau", " ci,cd ", "python", "sdlc", "ec2", "ecs", "s3", " elb ", " eb ",
                "scrum", "mobile",
                "rabbit", "zero mq", "apn", "notification", "couchbase", "minitab"]
    # Skill listesi

    cont = cont.replace("\n", " ")
    line = re.sub(r'[^.\w\s]', ",", cont)  # text manipulasyonu için (tamlamaları daha kolay detect edebilmek için)

    tokens = []
    anothertemp = []
    last = []

    if line:
        for e in keywords:  # skillerde dolaş
            if e in line.lower():  # linelarda varsa
                anothertemp.append(e)  # kelimeyi listedeki haliyle ekle
        doc = nlp(line)
        for token in doc.noun_chunks:  # line ı tokenlerine ayır (isim tamlamalarına)
            for key in keywords:
                if key in token.text.lower():  # eğer varsa
                    tokens.append(token.text)  # tamlama haliyle ekle
    flag = False
    for e2 in anothertemp:  # textte bulunan listedeki kelimelerin saf hallerinde kolaş
        for e in tokens:  # textte bulunan kelimelerin isim tamlamarında dolaş
            if e2 in e.lower():  # eğer listedeki saf hali, tamlama halinde varsa
                flag = True
                break  # alma
        if not flag:
            tokens.append(e2)  # yoksa al
        flag = False

    # yukarıdaki işlemin sebebi bazı skillerin isim tamlaması olarak görülmemesi

    for element in tokens:
        i = 0
        templist = []
        doc = nlp(element)
        for tok in doc:  # !!! DİKKAT BURASI TAMLAMA DEĞİL !!! ( HER BİR KELİME İÇİN BAKILIYOR)
            if tok.pos_ == "DET":  # a, the gibi ifadeleri alma
                pass
            else:
                templist.append(doc[i].text)
            i += 1
        last.append(" ".join(templist))

    last = list(set(last))
    return last


def getEducation(cont, data):

    univkeyword = ["university", "üniversite", "college"]
    notuniv = ["work", "degree"]

    majorkeyword = ["computer engineering", "informatic", "law", "information",
                    "science", "programming", "area", "field"]
    ismajor = ["degree", "bs", "bachelor", "master", "ms"]

    levelkeyword = ["master", "bachelor", "phd"]
    levelkeyword2 = ["bs", "ms"]


    doc = nlp(cont.replace("\n\n", " "))
    univ = []
    level = []
    major = []
    leveltemp = []

    flag = False
    for token in doc.noun_chunks:  # dolaş
        for key in univkeyword:  # universite anlatabilecek kelimelerde dolaş
            for forbid in notuniv:  # örneğin University Coursework gibi bir ifadeyi alma
                if key not in token.text.lower() or forbid in token.text.lower():
                    flag = True
                if flag == False:
                    univ.append(token.text)
        flag = False

    for line in cont.splitlines():
        for element in ismajor:
            if element in line.lower():
                doc = nlp(line)
                for token in doc.noun_chunks:
                    for key in majorkeyword:
                        if key in token.text.lower():  # bu ifade örneğin "" BS - MS - MASTER DEGREE IN COMPUTER ENGINEERING "" gibi satırlar için
                            major.append(token.text)

    for token in doc.noun_chunks:  # tokenlerde dolaş
        for key in levelkeyword:  # levele refer edebilecek ifadeleri bul
            if key in token.text.lower() and "degree" in token.text.lower():  # eğer degree ifadesi de varsa ekle
                level.append(token.text)

    pattern = re.compile(r'\w+\s*[\\/-]\s*\w+')  # BS/MS degree BS-MS degree bulmak için
    matches = pattern.findall(cont)
    for match in matches:
        for char in ["\\", "/", "-"]:
            if char in match:
                leveltemp.append(re.split(char, match))  # list of chardaki karakterlerle ayır
    for element in leveltemp:
        for part in element:
            for key in levelkeyword2:
                if key in part.lower():
                    level.append(part)  # her bir parçayı ekle

    level = list(set(level))
    data['EducationLevel'] = level
    univ = list(set(univ))
    data['University'] = univ
    major = list(set(major))
    data['EducationMajor'] = major


def getLocation(cont, data):
    last = []
    temp = []
    pattern = re.compile(r'[pP]lace.*|[lL]ocation.*')  # place ya da location içeren patternleri ara
    matches = pattern.findall(cont)

    if matches:
        for match in matches:
            doc = nlp(match)
            for token in doc:
                if token.pos_ == "PROPN" and token.tag_ == "NNP":  # özel isimlerii al
                    last.append(token.text)
        for element in last:
            doc = nlp(element)
            for token in doc.ents:
                if token.label_ == "GPE":  # Coğrafi bölge ya da yer adı içeren yerleri al
                    temp.append(token.text)

    temp = list(set(temp))

    data['Location'] = temp


def getExpertise(cont, data):

    expertisekeyword = ["developer", "science", "engineer", "development", "manager", "cloud",
                        "recruiter", "legal", "specialist", "coach", "cto", "cio"]
    cont = re.sub(r'[Ss]r.', "Senior", cont)
    cont = re.sub(r'[Jj]r.', "Junior", cont)
    lines = cont.splitlines()

    temp = []
    i = 0
    while True:
        firstline = lines[i]  # lineleri yukarıdan aşağı sırasıyla okumaya yarar
        doc = nlp(firstline)
        for token in doc.noun_chunks:  # listedekileri içeren ilk ifadeyi bulmak için dön
            for key in expertisekeyword:
                if key in token.text.lower():  # buldugun ilk ifade expertise
                    temp.append(token.text)
        if len(temp) > 0:
            break
        i += 1

    last = []
    for element in temp:
        doc = nlp(element)
        for token in doc.noun_chunks:
            i = 0
            templist = []
            doc2 = nlp(token.text)
            for key in expertisekeyword:
                if key in token.text.lower():
                    for tok in doc2:
                        if tok.tag_ == "NNP" or tok.tag_ == "NN" or tok.tag_ == "JJ":  ## NNP NN YA DA JJ ise al
                            templist.append(doc2[i].text)
                        else:
                            pass
                        i += 1
                    if len(templist) == 1:  # eğer tek kelime çıkarsa "engineering" gibi öncesini de al "..... engineering"
                        templist.insert(0, doc2[i - 2].text)  # bunun sebebi bazı isim tamlamalarının saptanamaması
                    last.append(" ".join(templist))
                    break

    data['expertise'] = last


def getmilitary(cont, data):
    pattern = re.compile(r'[mM]ilitary.*')
    icerik = pattern.findall(cont)
    temp = []
    for element in icerik:
        for key in ["completed", "done"]:
            if key in element.lower():
                temp.append(key)
    data['military'] = temp


# isblock ve makeblock fonksiyonlarının algoritmasını beraber yazdığimiz için açıklamıyorum

def isBlock(cont, l):
    pattern = re.compile(r'.*:\s')
    flags = pattern.findall(cont)
    for flag in flags:
        if flag in l:
            return True

    return False


def makeBlock(cont):
    flag = False
    block = []
    blocks = []
    cont = re.sub(r':', ": \n", cont)  # ":" içeren ifadelerden sonra 1 satır boşluk ver
    cont = cont.replace(u'\xa0', u' ')  # alfabe dışı gelen karakterleri yok et
    for l in cont.splitlines():
        if isBlock(cont, l):
            if not flag:
                flag = True
                blocks.append(block)
                block = [l]
            else:
                if len(block) != 0:
                    blocks.append(block)
                block = [l]
        else:
            if l != "":
                block.append(l)
    blocks.append(block)  # son blok ekle
    return blocks


def getSkills(blocks, data):

    prefkeyword = ["prefer", "nice to", "good to", "better"]
    mustkeyword = ["must", "have to"]
    numbers = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


    preferably = []
    must = []
    expected = []
    if len(blocks) != 1:  # block sayısı 1 den fazlaysa (en az 1 block dönecek)
        for block in blocks:  # blocklarda dolaş
            templist = []
            for i in range(0, len(block)):  # blockun içindeki her bir lineda dolaşılacak
                templist.append(block[i])  # listeye at
            tempstring = " \n ".join(templist)  # her lineyi newline ile böl
            foradd = getSkillLine(tempstring)  # skilleri çıkar
            if len(foradd) > 0:  # skiller varsa
                flag = False  # flag tut
                for prefkey in prefkeyword:  # prefkeylerde dolaş
                    if prefkey in block[0].lower():
                        flag = True  # buldum
                        if "year" in block[0].lower():  # lineda year varsa
                            key = ""
                            keyflag = False
                            for number in numbers:
                                if number in block[0].lower():  # yazılarda ara
                                    key = number + "+ preferably"
                                    keyflag = True  # buldum
                                    break
                            if not keyflag:
                                pattern = re.compile(r'\d')
                                matches = pattern.findall(block[0])
                                key = matches[0] + "+ preferably"
                            data[key] = foradd
                        else:
                            preferably.append(foradd)
                        break
                if not flag:  # bulamadıysam .... aynı sekilde devam eder
                    for mustkey in mustkeyword:
                        if mustkey in block[0].lower():
                            flag = True
                            if "year" in block[0].lower():
                                key = ""
                                keyflag = False
                                for number in numbers:
                                    if number in block[0].lower():
                                        key = number + "+ must"
                                        keyflag = True
                                        break
                                if keyflag == False:
                                    pattern = re.compile(r'\d')
                                    matches = pattern.findall(block[0])
                                    key = matches[0] + "+ must"
                                data[key] = foradd
                            else:
                                must.append(foradd)
                            break
                if not flag:
                    if "year" in block[0].lower():
                        pattern = re.compile(r'\d')
                        matches = pattern.findall(block[0])
                        key = matches[0] + "+ expected"
                        data[key] = foradd
                    else:
                        expected.append(foradd)
        if preferably:
            data["preferably"] = preferably
        if must:
            data["must"] = preferably
        if expected:
            data["expected"] = expected
    else:
        tempstring = " \n ".join(blocks[0])
        data["skills"] = getSkillLine(tempstring)


def main(path):
    data = {}
    path = path.split("\\")
    path = "\\".join([path[-2], path[-1]])
    content = getContent(path)
    getExpertiseLevel(content, data)
    getLanguageLine(content, data)
    getEducation(content, data)
    getLocation(content, data)
    getExpertise(content, data)
    getmilitary(content, data)
    getSkills(makeBlock(content), data)
    name = path.replace("docx\\", "json\\")
    name = name.replace(".docx", "")
    name = name + ".json"
    data = json.dumps(data)
    with open(name, "w") as f:
        f.write(data)


'''
    paths = getAllPaths()
    for i in range(0, len(paths)):
        data = {}
        content = getContent(paths[i])
        getExpertiseLevel(content, data)
        getLanguageLine(content, data)
        getEducation(content, data)
        getLocation(content, data)
        getExpertise(content, data)
        getmilitary(content, data)
        getSkils(makeBlock(content), data)
        name = paths[i].replace("docx\\","json\\")
        name = name.replace(".docx", "")
        name = name+".json"
        data = json.dumps(data)
        with open(name, "w") as f:
            f.write(data)
'''
