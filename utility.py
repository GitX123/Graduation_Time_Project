import mechanicalsoup
from jsonschema import validate

def university_num(university: str) -> int:
    if(university == 'NCTU'):
        return 0
    elif(university == 'NCU'):
        return 1
    elif(university == 'NTHU'):
        return 2
    elif(university == 'NYMU'):
        return 3
    else:
        raise ValueError

def start_year(university: str, student_id: str) -> str:
    year = None
    if university == 'NCTU':
        if(student_id[0] == '0'):
            year = '1' + student_id[0: 2]
        else:
            year = student_id[0: 2]

    elif university == 'NTHU' or university == 'NCU':
        if(student_id[0]=="1"):
            year = student_id[0: 3]
        else:
            year = student_id[0: 2]

    elif university == 'NYMU':
        if(student_id[0] == '0'):
            year = '1' + student_id[1: 3]
        else:
            year = student_id[1: 3]
    
    return year

# [TODO]
def graduation_time(professor, revision_time, student_obj_list, result):
    # open page of NDLTD
    base_url = 'https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi/'
    url = base_url + 'login?o=dwebmge'
    browser = mechanicalsoup.StatefulBrowser()
    browser.open(url)

    # search accordingly
    browser.select_form('form[name="main"]')
    browser["qs0"] = professor # [text] search bar
    browser["dcf"] = "ad" # [checkbox] filter (by professor)
    browser.submit_selected()

    # filter search results
    browser.select_form('form[name="main"]')
    browser['sortby'] = '-yr' # [select] sort (by graduation year in descending order)
    browser["SubmitChangePage"] = "1" # [hidden] renew page

    # --- retrieve data ---
    ccd = 'ccd=' + browser.get_url()[52:58:]
    record_url = base_url + ccd + '/record?r1=' # url prefix for entries of theses

    i, j = 0, 0
    threshold = 30
    while i < len(student_obj_list) and j < threshold:
        # open the page
        url = record_url + str(j + 1)
        browser.open(url)
        
        page = browser.get_current_page()

        # filter out PhD students
        degree = page.body.form.div.table.tbody.tr.td.table.find("th",text="學位類別:").find_next_sibling().get_text()
        if(degree != '碩士'):
            j += 1    
            continue

        student_name = page.body.form.div.table.tbody.tr.td.table.find("th", text="研究生:").find_next_sibling().get_text()
        if student_name == student_obj_list[i]['name']:
            oral_time = page.body.form.div.table.tbody.tr.td.table.find("th", text="口試日期:").find_next_sibling().get_text()
            grad_time = (float(oral_time.split('-')[0]) - 1911) + float(oral_time.split('-')[1]) / 12.0 # ROC year + month
            result.get('student_obj').append({
                'name': student_name,
                'id': student_obj_list[i].get('id'),
                'time_cost': round(grad_time - student_obj_list[i].get('start_time') + revision_time, 2)
            })
        else:
            # [TODO] Search for other records (if names do not match)
            pass

        i += 1
        j += 1

def search(data, count=10, start_month=7.0, revision_time=2.0/12):
    result = {'student_obj': []}

    # validate input
    schema = {
        'type': 'object',
        'properties': {
            'university': {'type': 'string'},
            'name': {'type': 'string'},
        },
    }
    validate(instance=data, schema=schema)

    # open page of UST theses
    base_url = 'http://etd.lib.nctu.edu.tw/cgi-bin/gs32/gsweb.cgi/'
    url = base_url + 'login?o=dwebmge'
    browser = mechanicalsoup.StatefulBrowser()
    browser.open(url)

    # search accordingly
    browser.select_form('form[name="main"]')
    browser["qs0"] = data.get('name') # [text] search bar
    browser["dcf"] = "ad" # [checkbox] filter (by professor)
    browser["limitdb"] = university_num(data.get('university')) # [checkbox] filter (by university)
    browser.submit_selected()

    # filter search results
    browser.select_form('form[name="main"]')
    browser['sortby'] = '-yr' # [select] sort (by graduation year in descending order)
    browser["SubmitChangePage"] = "1" # [hidden] renew page

    # retrieve data
    ccd = 'ccd=' + browser.get_url()[54: 60]
    record_url = base_url + ccd + '/record?r1=' # url prefix for entries of theses  

    i, j = 0, 0
    threshold = 30 # prevent from looping forever

    student_obj_list = []
    while i < count and j < threshold:
        # open the page
        url = record_url + str(j + 1)
        browser.open(url)
        page = browser.get_current_page()

        # filter out PhD students
        degree = page.body.form.div.table.tbody.tr.td.table.find("th", text="學位類別:").find_next_sibling().get_text()
        if(degree != '碩士'):
            j += 1    
            continue

        # calculate start and graduation time
        try:
            student_name = page.body.form.div.table.tbody.tr.td.table.find("th", text="作者:").find_next_sibling().get_text()
        except AttributeError:
            student_name = page.body.form.div.table.tbody.tr.td.table.find("th", text="作者(中文):").find_next_sibling().get_text()
        student_id = page.body.form.div.table.tbody.tr.td.table.find("th", text="學號:").find_next_sibling().get_text()
        start_time = float(start_year(data.get('university'), student_id)) + start_month / 12.0

        if(start_time != None):
            student_obj_list.append({
                'name': student_name,
                'id': student_id,
                'start_time': start_time
            })
        i += 1
        j += 1

    # store the results
    graduation_time(data.get('name'), revision_time, student_obj_list, result)

    # average graduation time
    avg_time = 0.0
    for r in result.get('student_obj'):
        avg_time += r.get('time_cost') / len(result['student_obj'])
    result.update({'avg_time': round(avg_time, 2)})

    return result