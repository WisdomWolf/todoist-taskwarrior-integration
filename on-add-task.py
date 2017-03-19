#!/usr/bin/env python
from datetime import datetime
import todoist
import json
import time
import sys
import os

# load config
try:
    with open(os.path.join(os.path.expanduser('~'), '.task', 'hooks', 'config.json'), 'r') as configFile:
        config = json.load(configFile)
except Exception:
    print('Failed to load config.')
    sys.exit(1)

# capture input
task = sys.stdin.readline()
new_task = json.loads(task)

# check that config is correct
if not 'user' in config or not 'username' in config['user'] or not 'password' in config['user']:
    print('Failed to read config properly. Can''t upload to Todoist.')
else:
    # connect to todoist
    api = todoist.TodoistAPI()
    user = api.user.login(config['user']['username'], config['user']['password'])
    resp = api.sync()
    projects = resp['projects']
    prev_task_ids = [f['id'] for f in resp['items']]

    # gather the parts of the task that are useful for todoist
    if 'description' in new_task:
        title = new_task['description']
    else:
        title = ''
    if 'project' in new_task:
        proj = new_task['project']
    else:
        proj = 'Inbox'
        new_task['project'] = proj
    if 'due' in new_task:
        date = datetime.strptime(new_task['due'], '%Y%m%dT%H%M%SZ')
    else:
        date = ''

    # find the corresponding project id & upload to todoist
    if proj in [f['name'] for f in projects]:
        remote_proj = [f['id'] for f in projects if f['name'] == proj][0]
    elif not proj == 'Inbox':
        # add project remotely
        temp_id = api.projects.add(proj)['id']
        remote_proj = api.commit()['temp_id_mapping'][temp_id]
    else:
        remote_proj = [f['id'] for f in projects if f['name'] == 'Inbox'][0]
    if not date == '':
        item = api.items.add(title,
                             project_id = remote_proj,
                             due_date_utc = date.strftime('%Y-%m-%dT%H:%M'),
                             date_string = date.strftime('%Y-%m-%dT%H:%M'))
    else:
        item = api.items.add(title,
                             project_id = remote_proj)
    # commit the new task to Todoist, then determine what uuid was assigned and record it on the local task.
    try:
        tdi_id = api.commit()['temp_id_mapping'][item['id']]
    except KeyError:
        tdi_id = str(int(item['id']))
    new_task['tdi_uuid'] = tdi_id
    print('Uploaded task to todoist.')

# write out the task to taskwarrior
print(json.dumps(new_task))
sys.exit(0)
