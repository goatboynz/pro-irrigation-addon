# 🚀 Start Here - Upload to GitHub

Welcome! Your Pro-Irrigation v2 add-on is ready to upload to GitHub and install in Home Assistant.

## Quick Setup (5 minutes)

### Step 1: Replace Images ⚠️

**IMPORTANT**: Replace these placeholder files with actual images:

- `icon.png` - 512x512 PNG (for add-on store)
- `logo.png` - 256x256 PNG (for add-on details)

Find free icons at:
- https://www.flaticon.com (search "sprinkler")
- https://icons8.com
- https://www.iconfinder.com

### Step 2: Run Setup Script

**On Windows:**
```cmd
setup-github.bat
```

**On Linux/Mac:**
```bash
chmod +x setup-github.sh
./setup-github.sh
```

The script will:
1. Initialize Git repository
2. Ask for your GitHub username
3. Configure remote repository
4. Push your code to GitHub

### Step 3: Install in Home Assistant

1. Open Home Assistant
2. Go to **Settings** → **Add-ons** → **Add-on Store**
3. Click **⋮** (three dots) → **Repositories**
4. Add: `https://github.com/YOUR_USERNAME/pro-irrigation-addon`
5. Find "Pro-Irrigation v2" and click **Install**
6. Click **Start**
7. Enable **Show in sidebar**

## That's It! 🎉

Your add-on is now installed and ready to use.

## What's Included

✅ Complete Home Assistant add-on
✅ FastAPI backend with API docs
✅ Vue.js frontend
✅ Comprehensive documentation
✅ GitHub Actions for automated builds
✅ Installation guides
✅ Deployment checklist

## Documentation Files

- **README.md** - Full documentation
- **INSTALL.md** - Installation guide
- **QUICK_START.md** - 5-minute quick start
- **GITHUB_SETUP.md** - Detailed GitHub setup
- **DEPLOYMENT_CHECKLIST.md** - Pre-deployment checklist
- **SETUP_COMPLETE.md** - What's been set up

## Need Help?

1. **GitHub Setup**: See `GITHUB_SETUP.md`
2. **Installation**: See `INSTALL.md`
3. **Quick Start**: See `QUICK_START.md`
4. **Deployment**: See `DEPLOYMENT_CHECKLIST.md`

## Manual Setup (Alternative)

If you prefer manual setup:

1. Create repository on GitHub (public)
2. Initialize git: `git init`
3. Add remote: `git remote add origin https://github.com/YOUR_USERNAME/pro-irrigation-addon.git`
4. Commit: `git add . && git commit -m "Initial commit"`
5. Push: `git push -u origin main`

## Before You Deploy

Check the deployment checklist:
- [ ] Images replaced (icon.png, logo.png)
- [ ] Version numbers correct (2.0.0)
- [ ] Documentation reviewed
- [ ] Ready to support users

## Support

- **Issues**: https://github.com/YOUR_USERNAME/pro-irrigation-addon/issues
- **Discussions**: https://github.com/YOUR_USERNAME/pro-irrigation-addon/discussions

---

**Ready?** Run the setup script and let's get your add-on on GitHub! 🚀
