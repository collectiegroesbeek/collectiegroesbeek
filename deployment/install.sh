#!/bin/bash

# allow port forwarding
sudo sed -i -e '/^\(#\|\)AllowTcpForwarding/s/^.*$/AllowTcpForwarding yes/' /etc/ssh/sshd_config

# Update packages
sudo apt update

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx

# Install the downloaded Elasticsearch .deb file
sudo dpkg -i /opt/collgroesbeek/deployment/elasticsearch-*-amd64.deb
# If there are dependency issues, resolve them with
sudo apt-get install -f

# Backup the original config
sudo cp /etc/elasticsearch/elasticsearch.yml /etc/elasticsearch/elasticsearch.yml.bak
# Configure Elasticsearch for local access without security
sudo tee /etc/elasticsearch/elasticsearch.yml > /dev/null << 'EOF'
cluster.name: local-cluster
node.name: local-node
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 127.0.0.1
http.port: 9200
discovery.type: single-node
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false
EOF

# Enable and start Elasticsearch
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# Set up Python environment
cd /opt/collgroesbeek
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install uwsgi

# Copy .env file
cp /opt/collgroesbeek/deployment/.env /opt/collgroesbeek/.env

# Set up Nginx
sudo ln -sf /opt/collgroesbeek/deployment/nginx.conf /etc/nginx/sites-available/collgroesbeek
sudo ln -sf /etc/nginx/sites-available/collgroesbeek /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# Make folder for uwsgi logs
sudo mkdir /var/log/uwsgi
sudo chown www-data /var/log/uwsgi

# Set up systemd service for Flask
sudo ln -sf /opt/collgroesbeek/deployment/collgroesbeek.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable collgroesbeek
sudo systemctl restart collgroesbeek

# Configure HTTPS
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Installing HTTPS certificates
sudo certbot --nginx --non-interactive --agree-tos -d collectiegroesbeek.nl -d www.collectiegroesbeek.nl
sudo certbot renew --dry-run
