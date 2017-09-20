import requests
from bs4 import BeautifulSoup


class Constant(object):
    def __init__(self, name, value, descr):
        self.name = name
        self.value = value
        self.descr = descr


def main():
    enum_name = input("Please enter the enum name to retrieve: ")
    # enum_name = 'EnumDSSXMLStatus'

    nice_enum_name = enum_name[7:]

    url = "https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/reference/com/microstrategy/webapi/{}.html".format(enum_name)

    response = requests.get(url)
    doc = BeautifulSoup(response.text, 'lxml')

    indent = ' ' * 3  # Print adds one

    print("#"*80)
    print("")

    print("""
from enum import Enum


class {}(Enum):  # {}""".format(nice_enum_name, enum_name))

    descr_obj = doc.find('div', class_='jd-descr')
    if descr_obj:
        if descr_obj.p:
            descr = descr_obj.p.string
            if descr:
                descr = descr.replace('\n', ' ')
                descr = descr.replace('  ', ' ')
                print(indent, '"""')
                print(indent, descr)
                print(indent, '"""')
                print("")

    constants_objs = doc.find_all('div', class_='jd-details api apilevel-')
    constant_list = list()
    prefix = None
    for constant in constants_objs:
        name = constant.find('h4').contents[2].string.strip()
        tag_data_obs = constant.find_all('div', class_='jd-tagdata')
        descr = None
        value = None
        for tag_data in tag_data_obs:
            if 'jd-tagdescr' in tag_data['class']:
                descr = tag_data.string
                if descr:
                    descr = descr.replace('\n', ' ')
                    descr = descr.replace('  ', ' ')
            else:
                spans = tag_data.find_all('span')
                value = list(spans)[1].string
                value, hex = value.strip().split(' ',1)
                value = value.strip()
                try:
                    value = int(value)
                except ValueError:
                    pass
                hex = hex.strip()
        if prefix is None:
            prefix = name
        else:
            while prefix not in name:
                prefix = prefix[:-1]
        constant_list.append(Constant(name, value, descr))

    for constant in sorted(constant_list, key=lambda x: x.value):
        nice_name = constant.name[len(prefix):]
        print(indent, "{name} = {c.value}  # {c.name} {c.descr}".format(name=nice_name, c=constant))

if __name__ == '__main__':
    main()
