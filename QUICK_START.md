# Quick Start - Push to GitHub

Your repository is ready! Follow these steps to push to GitHub and install in Home Assistant.

## 1. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `pro-irrigation-addon`
3. Make it **Public**
4. **DO NOT** add README, .gitignore, or license
5. Click **Create repository**

## 2. Push Your Code

Copy your GitHub username, then run these commands (replace YOUR_USERNAME):

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/pro-irrigation-addon.git

# Rename branch to main (if needed)
git branch -M main

# Push code
git push -u origin main

# Push tags
git push origin v1.0.0
```

## 3. Update URLs

Edit these files and replace `YOUR_USERNAME` with your actual GitHub username:

- `config.yaml` - line 5
- `repository.json` - line 3
- `README.md` - multiple locations
- `INSTALLATION.md` - installation section

Then commit:
```bash
git add config.yaml repository.json README.md INSTALLATION.md
git commit -m "Update repository URLs"
git push
```

## 4. Install in Home Assistant

1. Open Home Assistant
2. Go to **Settings** → **Add-ons** → **Add-on Store**
3. Click ⋮ menu → **Repositories**
4. Add: `https://github.com/YOUR_USERNAME/pro-irrigation-addon`
5. Find "Pro-Irrigation" in the store
6. Click **Install**
7. Click **Start**
8. Enable **Show in sidebar**

## Done! 🎉

Your add-on is now installable from Home Assistant!

## What's Next?

- Test the installation
- Create a GitHub release (optional)
- Share on Home Assistant Community forum
- Add screenshots to README
- Create an icon.png file

## Need Help?

See `GITHUB_SETUP.md` for detailed instructions and troubleshooting.
