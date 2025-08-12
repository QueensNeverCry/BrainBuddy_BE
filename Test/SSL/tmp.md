# asdad

- 단순 로컬 테스트

```plain
openssl req -x509 -nodes -sha256 -days 825 \
  -newkey rsa:2048 \
  -keyout dev.key \
  -out cert.pem \
  -config localhost.cnf -extensions ext
```
