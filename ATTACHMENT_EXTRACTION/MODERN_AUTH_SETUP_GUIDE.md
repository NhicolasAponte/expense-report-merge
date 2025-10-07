# Modern Authentication Setup Guide for Organization-Managed Accounts

## Why BasicAuth Failed and Modern Auth is Required

**BasicAuth (App Passwords) is deprecated** for organizational Microsoft 365 accounts. Microsoft has disabled this for security reasons. **Modern Authentication (OAuth 2.0)** is now required.

## Microsoft Requirements for Organization-Managed Accounts

### 1. **Azure App Registration (IT Admin Required)**

**⚠️ Important: This requires IT Administrator privileges**

#### Steps for IT Admin:
1. **Go to Azure Portal**: https://portal.azure.com
2. **Navigate to**: Azure Active Directory → App registrations → New registration
3. **Configure Application**:
   ```
   Name: Work Email Extractor
   Supported account types: Accounts in this organizational directory only
   Redirect URI: Not required for device flow
   ```
4. **Copy Application (Client) ID**: Save this for CLIENT_ID
5. **Copy Directory (Tenant) ID**: Save this for TENANT_ID

#### API Permissions (Admin must configure):
```
Microsoft Graph → Application permissions:
- Mail.Read (Read mail in all mailboxes)
- Mail.ReadWrite (Read and write mail in all mailboxes)

OR

Microsoft Graph → Delegated permissions:
- Mail.Read (Read user mail) 
- Mail.ReadWrite (Read and write user mail)
- offline_access (Maintain access to data)
```

#### Admin Consent:
- **CRITICAL**: Admin must click "Grant admin consent" for the organization
- Without this, authentication will fail

### 2. **Environment Variables Setup**

Add to your `.env` file:
```bash
# Azure App Registration (from IT Admin)
CLIENT_ID=your-azure-app-client-id-from-admin
TENANT_ID=your-organization-tenant-id-from-admin

# Work account emails to process
WORK_EMAIL_ADDRESS=account1@company.com
WORK_EMAIL_ADDRESS_2=account2@company.com
WORK_EMAIL_ADDRESS_3=account3@company.com
```

### 3. **Required Packages**
```bash
pip install msal requests
```

## Using the Modern Extractor

### Basic Setup:
1. **Get Azure app details from IT admin**
2. **Update .env file** with CLIENT_ID and TENANT_ID
3. **Configure accounts** in WORK_EMAIL_ADDRESS variables
4. **Run the script**: `python modern_work_extractor.py`

### Configuration Options:
```python
# Which accounts to process
ACCOUNTS_TO_PROCESS = [1]        # Single account
ACCOUNTS_TO_PROCESS = [1, 2, 3]  # Multiple accounts
ACCOUNTS_TO_PROCESS = 'all'      # All configured accounts

# Search criteria
DATE_RANGE_DAYS = 30
SEARCH_KEYWORDS = ["Invoice", "Paystub", "Receipt", "Statement"]
```

## Authentication Flow

### First Run (Device Code Flow):
1. Script displays a device code and URL
2. **You visit the URL on any device**
3. **Enter the device code**
4. **Sign in with your work account**
5. **Grant permissions** (if prompted)
6. Script continues automatically

### Subsequent Runs:
- Tokens are cached automatically
- No re-authentication needed (until token expires)

## Advantages Over BasicAuth

### ✅ **Security & Compliance**
- Complies with Microsoft's modern security requirements
- Works with MFA-enabled accounts
- No app passwords to manage

### ✅ **Functionality**
- Rich Graph API features
- Better search and filtering
- Access to all mailbox folders
- Proper attachment handling

### ✅ **Future-Proof**
- Microsoft's recommended approach
- Will continue working as Microsoft evolves
- Regular token refresh

## Organizational Considerations

### **IT Admin Requirements:**
- Azure AD admin privileges required for app registration
- Must grant admin consent for mail permissions
- May need to whitelist the application

### **Security Policies:**
- Some organizations block new app registrations
- Conditional access policies may apply
- MFA requirements will be honored

### **Compliance:**
- Audit logs maintained in Azure AD
- Proper OAuth scopes limit access
- Centralized permission management

## Troubleshooting Common Issues

### **"Admin consent required"**
- IT admin must grant consent in Azure portal
- Cannot be bypassed by individual users

### **"Application not found"**
- CLIENT_ID is incorrect
- App may not be registered in your tenant

### **"Access denied"**
- User doesn't have permission to mailbox
- Admin consent not granted
- Incorrect tenant ID

### **"Device code expired"**
- User took too long to authenticate
- Re-run script to get new device code

## Alternative: Application Permissions

If you need **unattended access** (no user interaction), ask IT admin to:

1. **Configure Application Permissions** instead of delegated
2. **Create client secret** for the app
3. **Grant admin consent** for application permissions

This allows the script to run without user authentication but requires higher admin privileges.

## Script Comparison

| Feature | exchangelib_auth.py | modern_work_extractor.py |
|---------|-------------------|-------------------------|
| Authentication | BasicAuth (Deprecated) | OAuth 2.0 (Modern) |
| Org Accounts | ❌ Often blocked | ✅ Fully supported |
| MFA Support | ❌ Limited | ✅ Full support |
| IT Admin Required | No | Yes (one-time setup) |
| Future-Proof | ❌ Being deprecated | ✅ Microsoft recommended |
| Setup Complexity | Simple | Moderate (IT involvement) |

## Recommendation

**Use `modern_work_extractor.py`** for organization-managed accounts because:
- ✅ Works with modern security policies
- ✅ Complies with Microsoft requirements  
- ✅ Future-proof authentication
- ✅ Better API features
- ✅ Proper organizational support

The initial setup requires IT admin involvement, but once configured, it provides a much more robust and compliant solution for organizational email access.