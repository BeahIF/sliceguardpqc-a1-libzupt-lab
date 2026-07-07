$BaseUrl = "http://localhost:8085"

Write-Host "Criando policy type 2001..."

curl.exe -s -X PUT `
  "$BaseUrl/a1-p/policytypes/2001" `
  -H "Content-Type: application/json" `
  --data-binary "@policytype-2001.json"

Write-Host "Criando policy hospital..."

curl.exe -s -X PUT `
  "$BaseUrl/a1-p/policytypes/2001/policies/slice-hospital-security" `
  -H "Content-Type: application/json" `
  --data-binary "@hospital.json"

Write-Host "Criando policy industrial..."

curl.exe -s -X PUT `
  "$BaseUrl/a1-p/policytypes/2001/policies/slice-industry-security" `
  -H "Content-Type: application/json" `
  --data-binary "@industry.json"

Write-Host "Criando policy pública..."

curl.exe -s -X PUT `
  "$BaseUrl/a1-p/policytypes/2001/policies/slice-public-security" `
  -H "Content-Type: application/json" `
  --data-binary "@public.json"

Write-Host "Policies registradas:"

curl.exe -s `
  "$BaseUrl/a1-p/policytypes/2001/policies"

Write-Host ""