# Create your application directory
sudo mkdir -p /opt/collgroesbeek
# Set proper ownership
sudo chown www-data:www-data /opt/collgroesbeek
# Set proper permissions
sudo chmod 755 /opt/collgroesbeek
# Give group write permissions
sudo chmod g+w -R /opt/collgroesbeek
# Ensure future files maintain group ownership
sudo chmod g+s /opt/collgroesbeek
