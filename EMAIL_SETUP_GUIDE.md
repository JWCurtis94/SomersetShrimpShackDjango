# EMAIL NOTIFICATION SETUP GUIDE

## 📧 Email Notifications Implementation Complete!

I've implemented a comprehensive email notification system for your Somerset Shrimp Shack store. Here's what's been added:

### ✅ **What's Been Implemented:**

1. **Customer Order Confirmation Emails**
   - Professional HTML and plain text emails
   - Order details, items, pricing, and shipping info
   - Sent automatically when payment is confirmed

2. **Admin Order Notification Emails**
   - Urgent notification emails to store owner
   - Complete order details for processing
   - Sent to admin when new orders are received

3. **Email Templates Created:**
   - `store/templates/store/emails/order_confirmation.html`
   - `store/templates/store/emails/order_confirmation.txt`
   - `store/templates/store/emails/order_notification.html`
   - `store/templates/store/emails/order_notification.txt`

4. **Email Utility Functions:**
   - `store/utils.py` - Contains email sending functions
   - Proper error handling and logging
   - Configurable email settings

### 🔧 **Setup Required:**

#### Step 1: Configure Email Settings

Create or update your `.env` file with email credentials:

```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-business-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here

# Email addresses
DEFAULT_FROM_EMAIL=Somerset Shrimp Shack <noreply@somersetshrimp.com>
ADMIN_EMAIL=your-admin-email@gmail.com
```

#### Step 2: Gmail Setup (Recommended)

For Gmail accounts:

1. **Enable 2-Factor Authentication**
   - Go to Google Account settings
   - Security → 2-Step Verification → Turn on

2. **Generate App Password**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password
   - Use this password (not your regular Gmail password) in EMAIL_HOST_PASSWORD

3. **Update Environment Variables**
   ```bash
   EMAIL_HOST_USER=yourbusiness@gmail.com
   EMAIL_HOST_PASSWORD=abcd-efgh-ijkl-mnop  # The app password from step 2
   ADMIN_EMAIL=yourbusiness@gmail.com
   ```

#### Step 3: Test Email Configuration

Run the test command to verify emails work:

```bash
# Test basic email sending
python manage.py test_email --test-email your-email@example.com

# Test with an existing order (replace 1 with actual order ID)
python manage.py test_email --order-id 1
```

### 📧 **How It Works:**

1. **Customer Places Order** → Stripe processes payment
2. **Stripe Webhook Triggered** → Confirms payment success
3. **Automatic Emails Sent:**
   - Customer receives order confirmation
   - Admin receives order notification
4. **Stock Updated** → Inventory automatically adjusted

### 🛠 **For Development/Testing:**

During development, emails are printed to the console instead of being sent. To test actual email sending, set `DEBUG=False` in your environment or temporarily change the email backend in settings.

### 🚨 **Important Notes:**

1. **Admin Email Address**: Make sure to set `ADMIN_EMAIL` to the email where you want to receive order notifications.

2. **From Email**: The `DEFAULT_FROM_EMAIL` can be any email address, but using your business domain looks more professional.

3. **Gmail Limits**: Gmail has sending limits (500 emails/day for free accounts). For high volume, consider using services like SendGrid or Amazon SES.

4. **Security**: Never commit your actual email passwords to version control. Always use environment variables.

### 🧪 **Testing Steps:**

1. Set up email credentials in `.env`
2. Run `python manage.py test_email --test-email your-email@example.com`
3. Place a test order to verify automatic emails
4. Check both customer and admin inboxes

### 📞 **Support:**

If you encounter issues:
- Check spam/junk folders
- Verify Gmail app password is correct
- Ensure 2FA is enabled on Gmail
- Check Django logs for error messages

The email system is now ready to keep both you and your customers informed about every order! 🎉
