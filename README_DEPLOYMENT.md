# 🚀 Deploying Nudgly to Vercel

This guide will help you deploy your Nudgly app to Vercel for production use.

## 📋 Prerequisites

1. **GitHub Account** - To connect your repository
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
3. **Environment Variables** - Your API keys and configuration

## 🔧 Step 1: Prepare Your Repository

Your repository is already configured with:
- ✅ `vercel.json` - Vercel deployment configuration
- ✅ `api/index.py` - Serverless entry point
- ✅ `runtime.txt` - Python version specification
- ✅ Updated `requirements.txt` - With cloud dependencies

## 📤 Step 2: Push to GitHub

1. **Create GitHub Repository**:
   ```bash
   # Go to github.com and create a new repository named 'nudgly'
   ```

2. **Add GitHub Remote**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/nudgly.git
   git branch -M main
   git push -u origin main
   ```

## 🌐 Step 3: Deploy to Vercel

1. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Build Settings**:
   - Framework Preset: **Other**
   - Root Directory: **Leave empty**
   - Build Command: **Leave empty** (Vercel auto-detects)
   - Output Directory: **Leave empty**

3. **Set Environment Variables**:
   Add these in Vercel Dashboard → Settings → Environment Variables:

   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   APP_BASE_URL=https://your-app-name.vercel.app
   TZ=Europe/London
   DAILY_DIGEST_HOUR=8
   ALLOWED_SENDERS=whatsapp:+44Number1,whatsapp:+44Number2
   ```

## 🗄️ Step 4: Database Setup

### Option A: Vercel Postgres (Recommended)
1. In Vercel Dashboard → Storage → Create Database
2. Choose **Postgres**
3. Vercel will automatically set `POSTGRES_URL`

### Option B: External Database
1. Use services like:
   - **Supabase** (free tier available)
   - **PlanetScale** (MySQL)
   - **Railway** (PostgreSQL)
2. Set `POSTGRES_URL` environment variable

## 📱 Step 5: Configure Twilio Webhook

1. **Get Your Vercel URL**:
   - After deployment: `https://your-app-name.vercel.app`

2. **Update Twilio Webhook**:
   - Go to [Twilio Console](https://console.twilio.com)
   - Navigate to Messaging → Try it out → Send a WhatsApp message
   - Set webhook URL to: `https://your-app-name.vercel.app/twilio/whatsapp`

3. **Update APP_BASE_URL**:
   - In Vercel environment variables
   - Set to your actual Vercel URL

## 🧪 Step 6: Test Your Deployment

1. **Test Web Dashboard**:
   - Visit `https://your-app-name.vercel.app`
   - Login with your WhatsApp number
   - Add and manage tasks

2. **Test WhatsApp Integration**:
   - Send a message to your Twilio WhatsApp number
   - Try: "Remind me to test the app at 3pm"

## 🔧 Troubleshooting

### Common Issues:

1. **Build Fails**:
   - Check Python version in `runtime.txt`
   - Verify all dependencies in `requirements.txt`

2. **Database Connection Issues**:
   - Ensure `POSTGRES_URL` is set correctly
   - Check database permissions

3. **WhatsApp Messages Not Working**:
   - Verify Twilio webhook URL
   - Check `APP_BASE_URL` environment variable
   - Ensure `ALLOWED_SENDERS` includes your number

4. **Scheduler Not Working**:
   - Vercel serverless functions have limitations
   - Consider using Vercel Cron Jobs for scheduled tasks

## 📊 Monitoring

1. **Vercel Dashboard**:
   - Monitor function invocations
   - Check logs and errors

2. **Database Usage**:
   - Monitor database connections
   - Set up alerts for usage limits

## 🔄 Updates

To update your deployed app:
```bash
git add .
git commit -m "Update description"
git push origin main
```

Vercel will automatically redeploy!

## 💡 Production Tips

1. **Environment Security**:
   - Never commit `.env` files
   - Use Vercel's environment variable encryption

2. **Database Backups**:
   - Set up automated backups
   - Test restore procedures

3. **Monitoring**:
   - Set up error tracking (Sentry)
   - Monitor uptime (UptimeRobot)

4. **Custom Domain** (Optional):
   - Add your own domain in Vercel settings
   - Update `APP_BASE_URL` accordingly

---

🎉 **Your Nudgly app will be live and accessible worldwide!**
