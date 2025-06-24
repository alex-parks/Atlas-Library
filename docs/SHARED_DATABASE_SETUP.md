# 🗄️ Shared Database Setup Guide

## Overview

Blacksmith Atlas is designed to support both **local development** and **shared production** database access. This guide explains how to set up a shared database that multiple users can access simultaneously.

## 🏗️ Architecture

### Current Setup (Local Development)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User A    │    │   User B    │    │   User C    │
│             │    │             │    │             │
│ localhost   │    │ localhost   │    │ localhost   │
│   :8529     │    │   :8529     │    │   :8529     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Local DB A  │    │ Local DB B  │    │ Local DB C  │
│ (separate)  │    │ (separate)  │    │ (separate)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Shared Setup (Production)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User A    │    │   User B    │    │   User C    │
│             │    │             │    │             │
│   Network   │    │   Network   │    │   Network   │
│   Access    │    │   Access    │    │   Access    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │ Shared      │
                   │ ArangoDB    │
                   │ Server      │
                   │             │
                   │ All users   │
                   │ see same    │
                   │ assets      │
                   └─────────────┘
```

## 🚀 Setup Instructions

### Step 1: Set Up Central ArangoDB Server

#### Option A: Company Server
```bash
# Install ArangoDB on your company server
sudo apt-get update
sudo apt-get install arangodb3

# Configure for network access
sudo nano /etc/arangodb3/arangod.conf

# Add/modify these lines:
[server]
endpoint = tcp://0.0.0.0:8529

[server]
authentication = true

# Start ArangoDB
sudo systemctl start arangodb3
sudo systemctl enable arangodb3

# Check status
sudo systemctl status arangodb3
```

#### Option B: Cloud Server (AWS, Azure, GCP)
```bash
# Launch a cloud instance
# Install ArangoDB
# Configure security groups to allow port 8529
# Set up SSL certificates for secure access
```

### Step 2: Create Database and User

```bash
# Connect to ArangoDB shell
arangosh

# Create the database
db._createDatabase('blacksmith_atlas')

# Create a dedicated user for the application
require('@arangodb/users').save('atlas_user', 'your_secure_password')

# Grant permissions to the user
require('@arangodb/users').grantDatabase('atlas_user', 'blacksmith_atlas', 'rw')

# Exit
exit
```

### Step 3: Update Configuration

#### For Each User's Installation:

1. **Update the production configuration** in `backend/assetlibrary/config.py`:

```python
'production': {
    'hosts': ['http://your-company-server.com:8529'],  # Replace with your server
    'database': 'blacksmith_atlas',
    'username': 'atlas_user',
    'password': 'your_secure_password',
    'collections': {
        'assets': 'assets',
        'relationships': 'asset_relationships',
        'projects': 'projects',
        'tags': 'tags',
        'users': 'users'
    }
}
```

2. **Set environment variable** (optional):
```bash
# On Windows
set ATLAS_ENV=production

# On Linux/macOS
export ATLAS_ENV=production
```

### Step 4: Test Shared Access

Run the test script to verify everything works:

```bash
# Test connections
py test_shared_database.py --test

# Set up shared database
py test_shared_database.py --setup
```

### Step 5: Start the Application

```bash
# Start with production environment
npm run dev
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_ENV` | Environment to use (`development` or `production`) | `development` |
| `ARANGO_HOST` | ArangoDB server hostname | `localhost` |
| `ARANGO_PORT` | ArangoDB server port | `8529` |
| `ARANGO_USER` | Database username | `root` |
| `ARANGO_PASSWORD` | Database password | `` |

### Configuration File

The main configuration is in `backend/assetlibrary/config.py`:

```python
DATABASE = {
    'arango': {
        'development': {
            'hosts': ['http://localhost:8529'],
            'database': 'blacksmith_atlas',
            'username': 'root',
            'password': '',
        },
        'production': {
            'hosts': ['http://your-server.com:8529'],
            'database': 'blacksmith_atlas',
            'username': 'atlas_user',
            'password': 'secure_password',
        }
    }
}
```

## 🔒 Security Considerations

### Network Security
- Use HTTPS for production connections
- Configure firewall rules to restrict access
- Use VPN if accessing over public internet

### Database Security
- Create dedicated users with minimal permissions
- Use strong passwords
- Regularly rotate credentials
- Enable authentication

### SSL/TLS Setup
```bash
# Generate SSL certificates
openssl req -newkey rsa:2048 -new -x509 -days 365 -nodes -out arangodb.crt -keyout arangodb.key

# Configure ArangoDB to use SSL
[server]
endpoint = ssl://0.0.0.0:8529
ssl-keyfile = /path/to/arangodb.key
ssl-certfile = /path/to/arangodb.crt
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if ArangoDB is running
   - Verify port 8529 is open
   - Check firewall settings

2. **Authentication Failed**
   - Verify username/password
   - Check user permissions
   - Ensure database exists

3. **Network Timeout**
   - Check network connectivity
   - Verify server is accessible
   - Check DNS resolution

### Debug Commands

```bash
# Test network connectivity
telnet your-server.com 8529

# Check ArangoDB status
curl http://your-server.com:8529/_api/version

# Test database connection
arangosh --server.database blacksmith_atlas --server.username atlas_user
```

## 📊 Monitoring

### Database Statistics
```bash
# Connect to ArangoDB shell
arangosh

# Check database stats
db._query('FOR doc IN assets COLLECT WITH COUNT INTO length RETURN length')

# Check user activity
db._query('FOR doc IN _users RETURN doc')
```

### Log Monitoring
```bash
# Check ArangoDB logs
sudo tail -f /var/log/arangodb3/arangod.log

# Check application logs
tail -f backend/logs/atlas.log
```

## 🔄 Migration from Local to Shared

If you're migrating from local development to shared production:

1. **Backup local data**:
```bash
# Export local database
arangodump --server.database blacksmith_atlas --output-directory backup/
```

2. **Set up shared database** (follow steps above)

3. **Import data**:
```bash
# Import to shared database
arangorestore --server.database blacksmith_atlas --input-directory backup/
```

4. **Update all users** to use production configuration

5. **Test thoroughly** before switching over

## 📝 Best Practices

1. **Always use dedicated users** for applications
2. **Regular backups** of the shared database
3. **Monitor performance** and scale as needed
4. **Document changes** and configurations
5. **Test in development** before production changes
6. **Use environment variables** for sensitive data
7. **Implement proper error handling** in applications

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review ArangoDB documentation
3. Check application logs
4. Test network connectivity
5. Verify configuration settings

For additional help, refer to the main project documentation or create an issue in the project repository. 