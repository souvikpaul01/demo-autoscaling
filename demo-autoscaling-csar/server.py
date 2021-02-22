from flask import json
from flask import request
from flask import Flask
import subprocess
import sys
import os

app = Flask(__name__)

@app.route("/")
def main():
    return "Welcome to Flask http server"


@app.route('/prometheus', methods=['POST'])

def webhook_api_prometheus():
    if request.headers['Content-Type'] == 'application/json':
        print ("json file received ")
        my_date = json.dumps(request.json)

        dict_info = json.loads(my_date)
        for i in dict_info['alerts']:
            alert =i['labels']['alertname']
            alert_loc = i['labels']['instance']
            print(alert,alert_loc)
            if(alert == 'HighCpuLoad'):
                print("Request for Scaling...")

                out = subprocess.Popen("ps -Alf | grep 'python scaleup.py' | wc | tr -s  \ | cut -f2 -d' '",stdout = subprocess.PIPE,shell =True)
                (numpro,err) = out.communicate()
                
                print(int(numpro))
                if int(numpro) <= 2 :
                    print('Scaling in Progress...')
                    os.system('python scaleup.py')
                else:
                   print("XOpera already running..Try again Later")
            
            elif(alert == 'LowCpuLoad'):
                print('Time to Scale Down')
            elif(alert == 'InstanceDown'):
                print('Restart Instance/Node exporter')
            else:
                print('some other thing')
        
        
        
        
        #subprocess.Popen(["bash", "/home/atiq/testScript.sh"]) 
                                  #Here you have to provide your script path and script name
        return (my_date)
    else:
        return("Connected Anyway")



#@app.route('/github', methods=['POST'])
#def api_github_message():
#    if request.headers['Content-Type'] == 'application/json':
#        print ("Great, you got the json data")
#        my_info = json.dumps(request.json)
#        print (my_info)
#        return (my_info)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5004)
