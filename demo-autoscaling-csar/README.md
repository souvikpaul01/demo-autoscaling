# Auto-Scaling of VM instances using Prometheus and xOpera Orchestrator
This demo presents detailed instructions on how to process the initial deployment of the service.yaml, automate the deployment of servers and other scalable components based on the alerts from the alertmanager, which are triggered based on the rules defined in Prometheus server.

In the following example, we used two components for scaling the OpenStack instances such as Webhook Autoscaler and Monitoring Server.

# Set-up Webhook Server/Autoscaler Agent
The initial requirement of this example is to install and set up the recent release of  Xopera orchestrator. This can be done from the quickstart guide, shown as follows:
```
https://github.com/xlab-si/xopera-opera
```
This steps of installing XOpera are demonstrated as follows:
```
$ sudo apt-get update
$ mkdir ~/opera && cd ~/opera
$ sudo apt-get install python3-venv
$ python3 -m venv .venv && . .venv/bin/activate
(.venv) $ pip install opera
```
The OpenStack modules from Ansible playbooks is quite common, thus we can install opera with all required OpenStack libraries by running the following command:
```
(.venv) $ pip install -U opera[openstack]
```
After setup of the XOpera and Openstack SDK, it is required to clone the github repository in the opera folder consisting of the autoscaler agent with the following command:
```
git clone https://github.com/radon-h2020/demo-policy-based-autoscaling
```
Change the working directory of the downloaded project. Before deploy the application, prepare the python environment and install necessary requirements. It is recommended that a Python virtual environment is used while installing the opera. This is an isolated and self-contained directory tree that contains a particular version of Python and installs additional packages.
```
cd demo-policy-based-autoscaling
```
In the virtual environment, configure the requirements for python using pip

```
pip install flask
pip install ruamel.yaml
```
Now the main components of the auto-scaler agent are set up. In order to have access to the Openstack environment, where the VM instances are deployed, Openstack SDK is used to get access to the environment. For this, initially download the Openstack RC file(ldpc-openrc.sh) and use the following command

```
(.venv) $ source ldpc-openrc.sh
(.venv) $ nova list
```
If the ‘nova list’ gives the list of servers deployed in Openstack, it confirms the connection is established. Next to make sure that the servers can be deployed and accessed with the same ssh key. This can be established with the following commands

```
(.venv) $ eval `ssh-agent`
(.venv) $ ssh-add pathToKey/KeyName.pem
(.venv) $ ssh-add -L
```
Now access configurations are done. The initial/base deployment of the server before starting the auto-scaler agent, assuming that the service.yaml file is ready to use
```
(.venv) $ opera deploy service.yaml
```
Finally, in order to start the webhook server for receiving the alerts from the alertmanager and trigger the autoscaler for the Scale-Up/Scale-Down, following file is used
```
(.venv) $ python server.py
```
 If the setup is done correctly and webhook is running, the following block is shown as output
 
 ```
(.venv) $ python server.py
 * Serving Flask app "server" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://0.0.0.0:5004/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 285-730-350
```
# Set-up Webhook Server/Autoscaler Agent
Configure prometheus and alertmanager, which are used to send alerts to the webhook server. The prometheus and alertmanager are set up manually on the monitoring server. Here, we assume that the user has already downloaded and installed prometheus and alertmanager in the monitoring server. This can be done from the official guide of Prometheus [here](https://prometheus.io/docs/prometheus/latest/installation/) and Alertmanager [here](https://prometheus.io/docs/alerting/latest/alertmanager/).

For the prometheus and alertmanager, it is important to keep the files in the dir /etc/prometheus and /etc/alertmanager and the prometheus.service and alertmanager.service files in /etc/systemd/system.

Assuming that the user is in the /home/ubuntu, and the configurations can be changed or modified default using the following steps
# Create or Update the prometheus.service
```
$ cd /etc/systemd/system
$ sudo nano prometheus.service
```
And copy the following steps in the prometheus.service file
```
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
```
# Create or Update the alertmanager.service
```
$ cd /etc/systemd/system
$ sudo nano alertmanager.service
```
And copy the following steps in the alertmanager.service file
```
[Unit]
Description=AlertManager Server Service
Wants=network-online.target
After=network-online.target

[Service]
User=root
Group=root
Type=Simple
ExecStart=/usr/local/bin/alertmanager \
    --config.file /etc/alertmanager/alertmanager.yml

[Install]
WantedBy=multi-user.target
```
# Create or Update alertmanager.yml

```
$ sudo nano /etc/alertmanager/alertmanager.yml
```

And copy the following steps in the alertmanager.yml file
```
global:
  resolve_timeout: 20s

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://webhookIp:5004/prometheus'
```
# Create or Update prometheus.yml
```
$ sudo nano /etc/prometheus/prometheus.yml
```
And copy the following steps in the prometheus.yml file
```
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).
# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - localhost:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  - "alert_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
    - targets: ['localhost:9090']

  - job_name: node-exporters
    static_configs:
      - targets: ['localhost:9100','targetIp:9100','172.17.67.188:9100','172.17.65.63:9100']
```
# Create or Update alert_rules.yml
```
$ sudo nano /etc/prometheus/alert_rules.yml
```
And copy the following steps in the alert_rules.yml file

```
groups:
 - name: example
   rules:
   - alert: InstanceDown
     expr: up == 0
     for: 1m

   - alert: HighCpuLoad
     expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[1m])) * 100) > 80
     for: 1m
   - alert: LowCpuLoad
     expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[1m])) * 100) < 20
     for: 1m
```
Now, all the configuration files and rules are defined, then start the alertmanager and prometheus services based on the following commands
```
$ sudo systemctl daemon-reload
$ sudo systemctl start alertmanager
$ sudo systemctl start prometheus
```
Now, the services running time is used to check their status if they are running properly
```
$ sudo systemctl status prometheus
```

# Acknowledgement

This project has received funding from the European Union’s Horizon 2020 research and innovation programme under Grant Agreement No. 825040 (RADON)
