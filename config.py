import configparser

def config(section='Paths'):
    parser = configparser.ConfigParser()
    parser.read('app.properties')
    params = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            params[item[0]] = item[1]
    else:
        raise Exception(f'Section {section} not found in the app.properties file')
    return params
