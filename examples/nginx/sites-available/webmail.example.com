server {
    listen 192.168.1.10:80;
    server_name     webmail.example.com;
    location / {
        proxy_pass http://192.168.1.18;
        proxy_set_header  X-Real-IP  $remote_addr;
        proxy_set_header  Host  $http_host;
    }
}
server {
    listen  192.168.1.10:443;
    server_name  webmail.example.com;
    ssl  on;
    ssl_certificate  /etc/nginx/ssl/example.com/cert/wildcard.example.com.pem;
    ssl_certificate_key  /etc/nginx/ssl/example.com/private/wilrdcard.example.com.key;
    ssl_session_timeout  5m;
    ssl_protocols  SSLv3 TLSv1;
    ssl_ciphers  ALL:!ADH:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv3:+EXP;
    ssl_prefer_server_ciphers   on;
    location / {
        proxy_pass https://192.168.1.18:443;
        proxy_set_header  X-Real-IP  $remote_addr;
        proxy_set_header  Host  $http_host;
    }
}
