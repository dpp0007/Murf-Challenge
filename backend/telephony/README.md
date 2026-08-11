# SIP Bridge Configuration (Asterisk)

This directory contains the Asterisk SIP bridge configuration for Kisan Mitra outbound weather alerts via Linphone.

## What is This?

The SIP bridge (Asterisk) is an intermediary that:

1. **Receives** outbound call requests from Kisan Mitra backend
2. **Routes** calls to the Linphone SIP service (sip.linphone.org)
3. **Handles** SIP protocol translation
4. **Manages** audio RTP streams between Linphone and the backend

```
Backend → SIP Bridge (Asterisk) → Linphone SIP Service → Linphone App
```

## Files

- `docker-compose.yml` - Docker Compose configuration to run Asterisk
- `asterisk_config/extensions.conf` - Call routing rules
- `asterisk_config/sip.conf` - SIP peer definitions and trunks
- `asterisk_config/rtp.conf` - RTP stream configuration
- `asterisk_config/logger.conf` - Logging configuration

## Quick Start

### Start Asterisk with Docker

```bash
# From this directory (backend/telephony/)
docker-compose up -d asterisk

# Verify it started
docker logs asterisk

# You should see: "Asterisk PBX startup complete"
```

### Verify SIP Port is Open

```bash
# Check if port 5060 is listening
netstat -an | grep 5060

# Should show:
# UDP  0.0.0.0:5060  0.0.0.0:*  (listening)
# TCP  0.0.0.0:5060  0.0.0.0:*  (listening)
```

### Stop Asterisk

```bash
docker-compose down
```

### View Logs

```bash
# Live logs
docker logs -f asterisk

# Last 50 lines
docker logs --tail 50 asterisk
```

## Configuration Details

### extensions.conf

Defines dial plan (how calls are routed):

- **weather_alert** context: Routes incoming weather alert calls to `linphone_account` peer
- Uses Asterisk's `Dial()` function to place calls

### sip.conf

Defines SIP peers and trunks:

- **linphone_account**: Outbound peer pointing to sip.linphone.org
- Handles SIP authentication and signaling
- Configures codec preferences (ulaw, alaw)
- Sets NAT handling for unreliable networks

### rtp.conf

RTP (Real-time Transport Protocol) configuration:

- **rtpstart/rtpend**: Port range 10000-10200 for audio streams
- **rtpbind**: Binds to all interfaces

### logger.conf

Logging configuration:

- Outputs to console and log files
- Log levels: debug, verbose, notice, warning, error, dtmf, fax

## Troubleshooting

### Asterisk won't start

```bash
# Check Docker logs
docker logs asterisk

# Rebuild
docker-compose build --no-cache asterisk

# Restart
docker-compose restart asterisk
```

### Port 5060 already in use

Change port in `docker-compose.yml`:
```yaml
ports:
  - "5061:5060/udp"  # Maps host 5061 to container 5060
```

And update `backend/.env.local`:
```bash
SIP_BRIDGE_PORT=5061
```

### SIP calls not routing

1. Check Linphone account is registered:
   - Open Linphone app
   - Settings → Accounts
   - Verify "Connected" status

2. Check Asterisk logs:
   ```bash
   docker logs asterisk | grep -i linphone
   ```

3. Verify SIP config:
   ```bash
   docker exec asterisk asterisk -rx "sip show peers"
   ```

## Advanced Configuration

### Register with Linphone (Direct Registration)

Uncomment in `sip.conf`:
```ini
register => username:password@sip.linphone.org
```

### Add Custom Extensions

Edit `extensions.conf` to add more dial contexts.

### Enable Debug Logging

Edit `sip.conf`:
```ini
sipdebug=yes
verbose_sip_events=yes
```

Then rebuild:
```bash
docker-compose build --no-cache
docker-compose up asterisk
```

## Security Considerations

⚠️ **Important for Production:**

1. **Don't expose port 5060** directly to the internet
   - Use a VPN or firewall
   - Use SIPS (SIP over TLS) on port 5061

2. **Secure SIP credentials**
   - Store passwords in environment variables
   - Use auth mechanisms in SIP config

3. **Monitor logs** for unauthorized access
   - Watch for "401 Unauthorized" messages
   - Check for suspicious call patterns

4. **Use TLS for SIP signaling**
   - Generate certificates
   - Configure in sip.conf

## Documentation

- [Asterisk Official Docs](https://wiki.asterisk.org/)
- [SIP Configuration Reference](https://wiki.asterisk.org/wiki/display/AST/SIP+Configuration+Examples)
- [Dialplan Guide](https://wiki.asterisk.org/wiki/display/AST/Dialplan)
- [Linphone Documentation](https://linphone.org/technical-help/)

## Related Documentation

See `docs/LINPHONE_SETUP.md` for the complete setup guide including:
- Creating Linphone SIP account
- Installing Linphone client
- Configuring backend
- Testing the system
- Troubleshooting common issues
