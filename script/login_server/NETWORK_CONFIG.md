# Network Configuration Guide

## Accessing the Login Server from Other Locations

### 1. Local Network Access
- Run the server with `host='0.0.0.0'`
- Find your computer's local IP address:
  - Windows: `ipconfig`
  - Mac/Linux: `ifconfig`
- Other devices can connect using: `http://<YOUR_LOCAL_IP>:5000`

### 2. Internet Access (Advanced)

#### Firewall Configuration
1. Open Windows Firewall:
   ```powershell
   # Allow incoming connections
   netsh advfirewall firewall add rule name="LoginServer" dir=in action=allow protocol=TCP localport=5000
   ```

#### Port Forwarding (Router Configuration)
1. Access router admin panel
2. Find Port Forwarding settings
3. Add new rule:
   - External Port: 5000
   - Internal Port: 5000
   - Internal IP: Your computer's local IP

#### Security Recommendations
- Use HTTPS
- Implement IP whitelisting
- Add two-factor authentication
- Use a reverse proxy (Nginx, Cloudflare)

### 3. Cloud Deployment Options
- Heroku
- AWS EC2
- DigitalOcean Droplet
- PythonAnywhere

### Potential Connection Scenarios
```python
# Local network
client = LoginClient('http://192.168.1.100:5000')

# Internet (after port forwarding)
client = LoginClient('http://your_public_ip:5000')

# Domain with SSL
client = LoginClient('https://login.yourdomain.com')
```

### Troubleshooting
- Check firewall settings
- Verify router configuration
- Ensure no conflicting services on port 5000
- Use `netstat -ano | findstr :5000` to check port usage
