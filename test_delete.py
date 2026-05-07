import urllib.request, urllib.parse, http.cookiejar, json
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

try:
    # Login
    data = urllib.parse.urlencode({'username': 'admin', 'password': '1234'}).encode('utf-8')
    resp = opener.open('http://127.0.0.1:5050/login', data=data)
    print('Login:', resp.status)

    # Create question
    create_data = urllib.parse.urlencode({'subject_id': 1, 'text': 'Test Question', 'description': ''}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:5050/admin/questions/add', data=create_data, method='POST')
    resp = opener.open(req)
    print('Create:', resp.status)

    # Get questions to find the ID
    req = urllib.request.Request('http://127.0.0.1:5050/admin/questions')
    resp = opener.open(req)
    html = resp.read().decode()
    import re
    match = re.search(r'action=\"/admin/questions/(\d+)/delete\"', html)
    if match:
        qid = match.group(1)
        print('Found Question ID:', qid)
        # Delete
        del_req = urllib.request.Request(f'http://127.0.0.1:5050/admin/questions/{qid}/delete', data=b'', method='POST')
        try:
            del_resp = opener.open(del_req)
            print('Delete:', del_resp.status)
        except urllib.error.HTTPError as e:
            print('Delete Error:', e.code, e.read().decode())
        except Exception as e:
            print('Delete Error:', e)
    else:
        print('No questions found')
except Exception as e:
    print('Error:', e)
