# Wushu-Alumni-Automatic-Email

A simple  script to send **personalized Gmail emails** to Columbia Wushu alumni (or any alumni).

### Features

* Reads sender credentials from a `.env` file (`EMAIL_USER`, `EMAIL_PASS`)
* Reads alumni contacts from a plaintext list such as:

  ```
  Andrew Andrew <Andrew@gmail.com>,
  Bobby Bobby <Bobby@columbia.edu>,
  Caleb Caleb <caleb@gmail.com>,
  ```
* Replaces `{{alumni_name}}` in the message body with each contact’s **first name**
* Sends messages via Gmail SMTP, adding a short delay between emails to avoid spam filters

---

### Setup

1. **Create a `.env` file** in the same folder:

   ```bash
   EMAIL_USER="youraddress@gmail.com"
   EMAIL_PASS="your_app_password_or_gmail_password"
   ```

   > If you use 2-Step Verification, generate a [Gmail App Password](https://myaccount.google.com/apppasswords).

2. **Create your alumni list file** (`alumni_list.txt`):

   ```bash
   Sunny Lai <sunnyxxlai@gmail.com>,
   Frederic Francoeur <rff2111@columbia.edu>,
   Caitlin Escudero <cdero14@gmail.com>,
   ```

3. **Run the script**:

   ```bash
   python send_alumni_emails.py --list alumni_list.txt
   ```

---

### Optional Flags

| Flag                                | Description                                     |
| ----------------------------------- | ----------------------------------------------- |
| `--dry-run`                         | Print emails instead of sending                 |
| `--delay 3.0`                       | Delay (in seconds) between sends (default: 3.0) |
| `--subject "..."`                   | Custom email subject                            |
| `--from-name "Columbia Wushu Team"` | Customize sender display name                   |

---

### Safety

Add these lines to your `.gitignore` to prevent leaking private info:

```
.env
.env.*
alumni_list.txt
*.csv
*.xlsx
```
