# Create .env file from template
Copy-Item .env.example .env

Write-Host "✅ Created .env file"
Write-Host "⚠️  Please edit .env and add your GROQ_API_KEY"
Write-Host ""
Write-Host "Get your free Groq API key at: https://console.groq.com"
