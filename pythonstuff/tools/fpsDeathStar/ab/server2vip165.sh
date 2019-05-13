#!/bin/bash
while true;
do
sleep 1.0;
   ab -k -c 50 -n 50 -H "Referer: http://10.26.1.119/login.aspx" -H "X-Forwarded-For:10.26.1.121" -H "WebSafeGuid:ZX1sMb0s6TC0" -H "FPS-License:9ae0daaf" -H "FPS-GeoIP: OC AU {Victoria}" -H "Content-Type: application/x-www-form-urlencoded" -H "MaxScore:0" -C "JSESSIONID=0001WiLvOXR-lR^CAjAI41B9Rg3:1b8aridbf; ClientGuid=ed3e45fbec148055145cadc0" -p ./post_body.txt http://10.30.22.165/stats/ &
done
