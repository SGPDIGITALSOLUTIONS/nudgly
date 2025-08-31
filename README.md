# Nudgly – Personal ADHD Reminder Assistant

A minimal, **WhatsApp-first reminder bot** for managing daily tasks through natural language voice notes and text messages. Built specifically for ADHD-friendly, frictionless task management.

> 🎯 **Goal**: Keep it simple - no complex UI, just chat with Nudgly via WhatsApp!

## ✨ Features

- 📱 **WhatsApp Integration** - Send reminders via text or voice notes
- 🎤 **Voice Transcription** - Speak your reminders naturally (OpenAI Whisper)
- 🧠 **Smart Parsing** - Natural language understanding for dates/times
- 📅 **Daily Digest** - Morning summary of today's tasks
- ⏰ **Smart Nudges** - Timely reminders when tasks are due
- 👥 **Trusted Circle** - Family members can add reminders
- 💾 **Simple Storage** - SQLite database, no complex setup

## 🛠️ Tech Stack

- **Python 3.11+** with FastAPI
- **SQLite + SQLAlchemy** for data storage
- **APScheduler** for reminder scheduling
- **Twilio WhatsApp** for messaging
- **OpenAI Whisper** for voice transcription
- **dateparser** for natural language date parsing

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+ installed
- FFmpeg installed (for voice note processing)
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

### 2. Setup

```bash
# Clone or create the project directory
cd nudgly

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```env
# Copy from env.example and fill in your values
cp env.example .env
```

Fill in your `.env` file with:

```env
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# OpenAI API Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Application Settings
APP_BASE_URL=https://your-ngrok-url.ngrok.io
TZ=Europe/London
DAILY_DIGEST_HOUR=8

# Allowed WhatsApp numbers (comma-separated)
ALLOWED_SENDERS=whatsapp:+447123456789,whatsapp:+447987654321
```

### 4. Get a Public URL (for Twilio webhooks)

Install and run ngrok:

```bash
# Install ngrok from https://ngrok.com/
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and update `APP_BASE_URL` in your `.env` file.

### 5. Configure Twilio WhatsApp

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging > Try it out > Send a WhatsApp message**
3. Set the webhook URL to: `https://your-ngrok-url.ngrok.io/twilio/whatsapp`
4. Save the configuration

### 6. Run Nudgly

```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
🚀 Starting Nudgly...
✅ Settings validated
✅ Database initialized
✅ Scheduler started
🎉 Nudgly is ready!
```

## 📱 How to Use

### Adding Reminders

Send any of these to your Twilio WhatsApp number:

**Text Messages:**
- `Remind me to take meds at 9am`
- `Call GP tomorrow at 11`
- `REMINDER: Pick up groceries tonight`

**Voice Notes:**
- Just record a voice message: "Remind me to put the bins out at 7pm"

### Managing Reminders

- **List today's reminders**: `LIST` or `What's today?`
- **List all reminders**: `LIST ALL`
- **Mark as done**: `DONE #123` or `DONE take meds`
- **Cancel reminder**: `CANCEL #123` or `CANCEL call GP`

### Daily Digest

Every morning at 8am (configurable), you'll receive a summary of the day's reminders:

```
🗓 Daily Digest - Monday, December 18

1. Take morning meds - 09:00
2. Call GP - 11:00
3. Pick up groceries - 18:00

📱 Reply with DONE [number] to mark complete
```

## 🏗️ Project Structure

```
nudgly/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── handlers.py          # WhatsApp webhook handlers
│   ├── scheduler.py         # APScheduler jobs
│   ├── parsers.py           # Natural language parsing
│   ├── whisper_utils.py     # Voice transcription
│   ├── models.py            # SQLAlchemy models
│   ├── db.py                # Database utilities
│   └── settings.py          # Configuration
├── requirements.txt
├── env.example
└── README.md
```

## 🗄️ Database Schema

### Reminders Table

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| created_by | String | Phone number who created it |
| for_user | String | Phone number who owns it |
| text | String | Reminder text |
| due_at | DateTime | When to send reminder (UTC) |
| status | String | PENDING/DONE/CANCELLED |
| source | String | text/voice |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (when implemented)
pytest
```

### Database Migrations

The app automatically creates tables on startup. For production, consider using Alembic:

```bash
# Initialize Alembic (optional)
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 🚀 Deployment

### Production Setup

1. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Set up a reverse proxy** (nginx/Apache)

3. **Use environment variables** for configuration

4. **Set up monitoring** and logging

### Environment Variables

For production, ensure these are set:

```bash
export TWILIO_ACCOUNT_SID=your_sid
export TWILIO_AUTH_TOKEN=your_token
export TWILIO_WHATSAPP_NUMBER=your_number
export OPENAI_API_KEY=your_key
export APP_BASE_URL=https://your-domain.com
export ALLOWED_SENDERS=whatsapp:+44...,whatsapp:+44...
```

## 🛠️ Troubleshooting

### Common Issues

1. **Voice notes not transcribing**
   - Check FFmpeg is installed: `ffmpeg -version`
   - Verify OpenAI API key is valid
   - Check audio format is supported (OGG, MP3, MP4, WAV)

2. **Webhook not receiving messages**
   - Ensure ngrok URL is HTTPS
   - Check Twilio webhook configuration
   - Verify allowed senders are correct

3. **Scheduler not working**
   - Check timezone setting in `.env`
   - Verify database permissions
   - Look for scheduler errors in logs

4. **Database errors**
   - Check SQLite file permissions
   - Ensure directory is writable
   - Try deleting `nudgly.db` to recreate

### Debug Mode

Set environment variable for more verbose logging:

```bash
export LOG_LEVEL=DEBUG
```

## 🔒 Security & Privacy

- **Minimal data storage** - only essential reminder information
- **Webhook validation** - Twilio request signatures verified
- **Number whitelist** - only allowed senders can use the bot
- **No sensitive data** - passwords/personal info not stored
- **Local storage** - SQLite database stays on your server

## 🗺️ Roadmap

### Next Features
- [ ] Recurring reminders (`every weekday at 9am`)
- [ ] Location-based reminders
- [ ] Reminder editing and snoozing
- [ ] Multiple time zones support
- [ ] Web dashboard for management
- [ ] Integration with calendar apps

### Nice to Have
- [ ] Natural language undo/edit
- [ ] Weekly summary reports
- [ ] Guardian mode (family members manage reminders)
- [ ] SMS fallback option
- [ ] Voice note playback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 💌 Support

- 📧 Email: support@nudgly.app
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/nudgly/issues)
- 💬 Discord: [Join our community](https://discord.gg/nudgly)

---

**Built with ❤️ for the ADHD community** 🧠✨

*Nudgly aims to make task management as frictionless as possible - because the best reminder system is the one you actually use.*
