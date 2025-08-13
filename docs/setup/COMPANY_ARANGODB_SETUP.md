# Connecting Blacksmith Atlas to Your Company's ArangoDB

This guide explains how to configure Blacksmith Atlas to automatically connect to your company's ArangoDB instance on startup.

## Quick Start

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your company's ArangoDB credentials:**
   ```bash
   # Edit with your preferred editor
   nano .env
   # or
   vim .env
   ```

3. **Update these required settings:**
   ```env
   ATLAS_ENV=production
   ARANGO_HOST=your-company-arangodb.com
   ARANGO_PORT=8529
   ARANGO_DATABASE=blacksmith_atlas
   ARANGO_USER=your_username
   ARANGO_PASSWORD=your_password
   ```

4. **Initialize the database (first time only):**
   ```bash
   pip install python-dotenv python-arango
   python scripts/init-company-db.py
   ```

5. **Start the application:**
   ```bash
   ./scripts/start-prod.sh
   ```

## Configuration Options

### Required Settings

- **ARANGO_HOST**: Your company's ArangoDB server hostname or IP address
- **ARANGO_USER**: Your ArangoDB username
- **ARANGO_PASSWORD**: Your ArangoDB password
- **ARANGO_DATABASE**: Database name (default: `blacksmith_atlas`)

### Optional Settings

- **ARANGO_PORT**: ArangoDB port (default: `8529`)
- **ASSET_LIBRARY_PATH**: Path to asset storage (default: `./assets`)
- **LOG_PATH**: Path for log files (default: `./logs`)
- **JWT_SECRET_KEY**: Secret key for authentication (generate a secure random string)

## SSL/TLS Configuration

If your company's ArangoDB uses SSL/TLS:

1. Update the configuration in `backend/assetlibrary/config.py`:
   ```python
   'hosts': [f"https://{os.getenv('ARANGO_HOST', 'arangodb')}:{os.getenv('ARANGO_PORT', '8529')}"],
   ```

2. Or create a custom environment variable:
   ```env
   ARANGO_PROTOCOL=https
   ```

## Using Different Environments

### Development (Local ArangoDB)
```bash
# Uses local ArangoDB container
podman compose up -d
```

### Production (Company ArangoDB)
```bash
# Uses external ArangoDB from .env
podman compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Connection Issues

1. **Check connectivity:**
   ```bash
   # Test if you can reach the ArangoDB server
   curl http://your-company-arangodb.com:8529/_api/version
   ```

2. **Verify credentials:**
   ```bash
   # Test authentication
   curl -u username:password http://your-company-arangodb.com:8529/_api/database
   ```

3. **Check logs:**
   ```bash
   podman logs blacksmith-atlas-backend
   ```

### Common Issues

- **"database not found"**: Run `python scripts/init-company-db.py` to create the database
- **"connection refused"**: Check if ARANGO_HOST is correct and accessible
- **"authentication failed"**: Verify username and password in .env
- **SSL errors**: Update to use `https://` in the connection URL

## Security Best Practices

1. **Never commit `.env` to version control**
   - The `.gitignore` already excludes it
   - Use `.env.example` as a template

2. **Use strong passwords**
   - Generate secure passwords for production use
   - Consider using a password manager

3. **Restrict database permissions**
   - Create a dedicated user for Blacksmith Atlas
   - Grant only necessary permissions

4. **Rotate credentials regularly**
   - Update passwords periodically
   - Use different credentials for different environments

## Database Management

### Initialize Database Structure
```bash
python scripts/init-company-db.py
```

This script will:
- Connect to your company's ArangoDB
- Create the `blacksmith_atlas` database (if needed)
- Create all required collections
- Set up indexes for performance

### Check Database Status
```bash
# View backend health and statistics
curl http://localhost:8000/health
```

### Backup Considerations
- Coordinate with your IT team for database backups
- Asset files in `ASSET_LIBRARY_PATH` should be backed up separately
- Consider implementing automated backup scripts

## Advanced Configuration

### Custom Database Names

If you need to use a different database name per environment:

```env
# Development
ARANGO_DATABASE=blacksmith_atlas_dev

# Staging  
ARANGO_DATABASE=blacksmith_atlas_staging

# Production
ARANGO_DATABASE=blacksmith_atlas_prod
```

### Multiple ArangoDB Clusters

For high availability setups with multiple coordinators:

1. Update `backend/assetlibrary/config.py`:
   ```python
   'hosts': [
       f"http://{os.getenv('ARANGO_HOST1')}:8529",
       f"http://{os.getenv('ARANGO_HOST2')}:8529",
       f"http://{os.getenv('ARANGO_HOST3')}:8529"
   ]
   ```

2. Set multiple hosts in `.env`:
   ```env
   ARANGO_HOST1=coordinator1.company.com
   ARANGO_HOST2=coordinator2.company.com
   ARANGO_HOST3=coordinator3.company.com
   ```

## Support

For issues specific to your company's ArangoDB setup:
1. Contact your database administrator
2. Check ArangoDB logs on the server
3. Verify network connectivity and firewall rules

For Blacksmith Atlas issues:
1. Check the application logs in `./logs`
2. Review the backend logs: `podman logs blacksmith-atlas-backend`
3. Consult the main documentation