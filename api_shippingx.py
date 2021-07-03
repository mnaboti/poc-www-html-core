import requests
import json
import platform
import subprocess
import os
from fabric import Connection

""" 
* get data from Xi
* @params url
* return dict
"""
def get_xi_data(url):
    response = requests.get(url)
    data = json.loads(response.text)
    data = data[0]['fields']
    return data

""" 
* sends SMS alerts
* @params url, params
* return dict
"""
def alert(url, params):
    headers = {'Content-type': 'application/json; charset=utf-8'}
    r = requests.post(url, json=params, headers=headers)
    return r

recipients = ["+265998006237", "+265991450316", "+265995246144", "+26599453942", "+265995971632", "+265888027458", "+265999755473", "+265992215557", "+265882680534", "+265997174007"]

cluster = get_xi_data('http://10.44.0.52/sites/api/v1/get_single_cluster/20')

for site_id in cluster['site']:
    site = get_xi_data('http://10.44.0.52/sites/api/v1/get_single_site/' + str(site_id))

    # functionality for ping re-tries
    count = 0

    while (count < 3):

        # lets check if the site is available
        param = '-n' if platform.system().lower()=='windows' else '-c'

        if subprocess.call(['ping', param, '1', site['ip_address']]) == 0:

            # shipping backup script
            #push_backup_script = "rsync " + "-r $WORKSPACE/devops_api_backup.sh " + site['username'] + "@" + site['ip_address'] + ":/var/www"
            #os.system(push_backup_script)
            
            # backing up application folder [API]
            #backup_script = "ssh " + site['username'] + "@" + site['ip_address'] + " 'cd /var/www && chmod 777 devops_api_backup.sh && ./devops_api_backup.sh'"
            #os.system(backup_script)
            
            # ship data to remote site
            push_api = "rsync " + "-r $WORKSPACE/BHT-EMR-API " + site['username'] + "@" + site['ip_address'] + ":/var/www"
            os.system(push_api)
            
            # run setup script
            run_api_script = "ssh " + site['username'] + "@" + site['ip_address'] + " 'cd /var/www/BHT-EMR-API && ./api_setup.sh'"
            os.system(run_api_script)
            
            result = Connection("" + site['username'] + "@" + site['ip_address'] + "").run('cd /var/www/BHT-EMR-API && git describe', hide=True)
            
            msg = "{0.stdout}"
            
            version = msg.format(result).strip()
            
            api_version = "v4.11.0"
            
            if api_version == version:
                msgx = "Hi there,\n\nDeployment of API to " + version + " for " + site['name'] + " completed succesfully.\n\nThanks!\nEGPAF HIS."
            else:
                msgx = "Hi there,\n\nSomething went wrong while checking out to the latest API version. Current version is " + version + " for " + site['name'] + ".\n\nThanks!\nEGPAF HIS."

            # send sms alert
            for recipient in recipients:
                msg = "Hi there,\n\nDeployment of API to " + version + " for " + site['name'] + " completed succesfully.\n\nThanks!\nEGPAF HIS."
                params = {
                    "tenant_id": "12345",
                    "recipient": recipient,
                    "message": msgx,
                    "message_category": "signup",
                    "brand_name": "EGPAF-HIS",    
                    "type": "internal"
                }
                alert("http://ec2-52-14-138-182.us-east-2.compute.amazonaws.com:56733/v1/sms/send", params)

            # close the while loop
            count = 3

        else:
            # increment the count
            count = count + 1

            # make sure we are sending the alert at the last pint attempt
            if count == 3:
                for recipient in recipients:
                    msg = "Hi there,\n\nDeployment of API to V4.11.0 for " + site['name'] + " failed to complete after several connection attempts.\n\nThanks!\nEGPAF HIS."
                    params = {
                        "tenant_id": "12345",
                        "recipient": recipient,
                        "message": msg,
                        "message_category": "signup",
                        "brand_name": "EGPAF-HIS",    
                        "type": "internal"
                    }
                    alert("http://ec2-52-14-138-182.us-east-2.compute.amazonaws.com:56733/v1/sms/send", params)

        






