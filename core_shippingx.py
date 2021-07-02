import requests
import json
import platform
import subprocess
import os

""" 
* Gets data from Xi API
* @param url
* returns json
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

recipients = ["+265998006237", "+265991450316", "+265995246144", "+265992182669"]

#* Get cluster details
cluster = get_xi_data('http://10.44.0.52/sites/api/v1/get_single_cluster/3')

for site_id in cluster['site']:
    site = get_xi_data('http://10.44.0.52/sites/api/v1/get_single_site/' + str(site_id))

    # functionality for ping re-tries
    count = 0

    while(count < 3):

        #* lets check if the site is available
        param = '-n' if platform.system().lower()=='windows' else '-c'
        if subprocess.call(['ping', param, '1', site['ip_address']]) == 0:
            
            # shipping backup script
            push_backup_script = "rsync " + "-r $WORKSPACE/devops_core_backup.sh " + site['username'] + "@" + site['ip_address'] + ":/var/www/html"
            os.system(push_backup_script)
            
            # backing up application folder [Core & ART]
            backup_script = "ssh " + site['username'] + "@" + site['ip_address'] + " 'cd /var/www/html && chmod 777 devops_core_backup.sh && ./devops_core_backup.sh'"
            os.system(backup_script)
            
            #* ship data to remote site
            push_core = "rsync " + "-r $WORKSPACE/BHT-Core " + site['username'] + "@" + site['ip_address'] + ":/var/www/html"
            os.system(push_core)

            # send sms alert
            for recipient in recipients:
                msg = "Hi there,\n\nDeployment of CORE to v4.8.0 for " + site['name'] + " completed succesfully.\n\nThanks!\nEGPAF HIS."
                params = {
                    "tenant_id": "12345",
                    "recipient": recipient,
                    "message": msg,
                    "message_category": "signup",
                    "brand_name": "EGPAF-HIS",    
                    "type": "internal"
                }
                alert("http://ec2-52-14-138-182.us-east-2.compute.amazonaws.com:56733/v1/sms/send", params)

            count = 3

        else:

            count = count + 1

            # make sure we are sending the alert at the last pint attempt
            if count == 3:
                for recipient in recipients:
                    msg = "Hi there,\n\nDeployment of CORE to v4.8.0 for " + site['name'] + " failed to complete after several connection attempts.\n\nThanks!\nEGPAF HIS."
                    params = {
                        "tenant_id": "12345",
                        "recipient": recipient,
                        "message": msg,
                        "message_category": "signup",
                        "brand_name": "EGPAF-HIS",    
                        "type": "internal"
                    }
                    alert("http://ec2-52-14-138-182.us-east-2.compute.amazonaws.com:56733/v1/sms/send", params)
