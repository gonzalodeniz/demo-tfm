{{/*
Return "true" when a value looks truthy, otherwise "false".
Accepts booleans or common string equivalents so ArgoCD --set strings still work.
*/}}
{{- define "monitoring.boolEnabled" -}}
{{- $v := . | toString | lower -}}
{{- if or (eq $v "true") (eq $v "1") (eq $v "yes") (eq $v "on") -}}
true
{{- else -}}
false
{{- end -}}
{{- end -}}
