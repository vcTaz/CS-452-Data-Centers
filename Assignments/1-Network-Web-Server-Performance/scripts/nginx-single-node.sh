#!/bin/bash
set -euo pipefail

sudo mkdir -p /var/www/app
sudo cp -a "$HOME/CS-452-Data-Centers/Assignments/1-Network-Web-Server-Performance/src/app/." /var/www/app/

sudo find /var/www/app -type d -exec chmod 755 {} +
sudo find /var/www/app -type f -exec chmod 644 {} +

sudo sed -i -E \
    's/^[[:space:]]*worker_processes[[:space:]]+[^;]+;/worker_processes 1;/' \
    /etc/nginx/nginx.conf

sudo tee /etc/nginx/sites-available/app > /dev/null <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    root /var/www/app;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
EOF

sudo ln -sfn /etc/nginx/sites-available/app /etc/nginx/sites-enabled/app

sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t

sudo systemctl enable --now nginx
sudo systemctl reload nginx

curl -I http://localhost/

echo "Nginx deployment completed."

