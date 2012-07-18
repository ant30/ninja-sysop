$TTL    3600
@       IN      SOA             ns1.example.admin. admin.example.com (
                2009092101      ;serial aaaammdd
                10800           ;refresh. 3 hours
                3600            ;retry. 1 hour
                432000          ;expire. 5 days
                86400 )         ;minimum. minium TTL (1 day)

@       IN      NS              ns1.example.com.
@       IN      NS              ns2.example.com.

@     A 127.0.0.1
www   A 127.0.0.1
ns1     A 127.1.0.1
ns2     A 127.1.0.2
mail    A 127.0.1.1

imap    CNAME mail
pop3    CNAME mail
webmail CNAME mail

svn 10 CNAME www2 ;Prueba de ttl en www2
hg  CNAME www
git CNAME www
desarrollo CNAME default
