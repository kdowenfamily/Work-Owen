#!/bin/bash
while true;
do
sleep 1.0;
ab -k -q -c 200 -n 200 -H "X-Forwarded-For:10.26.1.121" -H "FPS-License:9ae0daaf"  'http://10.30.22.164/stats/?client_request_uri=http://10.26.1.116%2flogin.aspx&fpm_additional_info=&fpm_alert_component=15&fpm_alert_details=&fpm_alert_id=d4&fpm_alert_type=1&fpm_guid=9d30bvfoBbDi&fpm_score=40&fpm_transaction_data=&fpm_url_name=%2flogin.aspx&http_referrer=&fpm_defined_value=&fpm_resolved_value=HTTP/1.1' &
done
