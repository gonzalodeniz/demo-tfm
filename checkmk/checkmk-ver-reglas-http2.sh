curl -X GET \
  "http://127.0.0.1:5000/cmk/check_mk/api/2.0/domain-types/rule/collections/all?ruleset_name=active_checks:httpv2" \
  -H "Accept: application/json" \
  -H "Authorization: Basic $(echo -n 'cmkadmin:admin123' | base64)"

