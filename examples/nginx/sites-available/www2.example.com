server {
    listen 192.168.1.10:80;
    server_name     www2.example.com;
    location / {
        proxy_pass http://192.168.1.14:8080;
        proxy_set_header  X-Real-IP  $remote_addr;
    }
}
