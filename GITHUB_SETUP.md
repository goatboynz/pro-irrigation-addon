# GitHub Setup Guide

This guide will help you push the Pro-Irrigation Add-on to GitHub and make it installable in Home Assistant.

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **+** icon in the top right corner
3. Select **New repository**
4. Fill in the details:
   - **Repository name**: `pro-irrigation-addon` (or your preferred name)
   - **Description**: Professional irrigation management system for Home Assistant
   - **Visibility**: Public (required for Home Assistant add-on store)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **Create repository**

## Step 2: Push to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/pro-irrigation-addon.git

# Verify the remote was added
git remote -v

# Push the code and tags
git push -u origin main
git push origin v1.0.0
```

**If you get an error about 'main' not existing**, your default branch might be 'master':
```bash
# Rename master to main
git branch -M main

# Then push
git push -u origin main
git push origin v1.0.0
```

## Step 3: Update Repository URLs

After pushing to GitHub, update these files with your actual GitHub username:

### 1. config.yaml
```yaml
url: https://github.com/YOUR_USERNAME/pro-irrigation-addon
```

### 2. repository.json
```json
{
  "name": "Pro-Irrigation Add-on Repository",
  "url": "https://github.com/YOUR_USERNAME/pro-irrigation-addon",
  "maintainer": "Your Name <your.email@example.com>"
}
```

### 3. README.md
Update all instances of:
- `https://github.com/yourusername/pro-irrigation-addon`

### 4. INSTALLATION.md
Update the repository URL in the installation instructions.

After updating, commit and push the changes:
```bash
git add config.yaml repository.json README.md INSTALLATION.md
git commit -m "Update repository URLs"
git push
```

## Step 4: Add to Home Assistant

Now you can install the add-on in Home Assistant:

### Method 1: Add Repository URL

1. Open Home Assistant
2. Go to **Settings** → **Add-ons** → **Add-on Store**
3. Click the three-dot menu (⋮) in the top right corner
4. Select **Repositories**
5. Add your repository URL:
   ```
   https://github.com/YOUR_USERNAME/pro-irrigation-addon
   ```
6. Click **Add**
7. Close the dialog
8. Refresh the page
9. Find "Pro-Irrigation" in the add-on store
10. Click **Install**

### Method 2: Direct Installation (Advanced)

If you have SSH access to Home Assistant:

```bash
# Clone the repository
cd /addons
git clone https://github.com/YOUR_USERNAME/pro-irrigation-addon.git

# Restart Home Assistant
ha core restart

# The add-on will appear in the Local add-ons section
```

## Step 5: Verify Installation

1. After installation, go to the add-on page
2. Click **Start**
3. Check the **Log** tab for any errors
4. Enable **Show in sidebar**
5. Click the sidebar icon to access the interface

## Step 6: Create a Release (Optional but Recommended)

Creating a GitHub release makes it easier for users to track versions:

1. Go to your repository on GitHub
2. Click **Releases** (on the right side)
3. Click **Create a new release**
4. Select the tag: **v1.0.0**
5. Release title: **v1.0.0 - Initial Release**
6. Description: Copy the content from CHANGELOG.md for version 1.0.0
7. Click **Publish release**

## Troubleshooting

### Repository Not Appearing in Home Assistant

- Verify the repository URL is correct
- Check that the repository is public
- Ensure `config.yaml` and `repository.json` are in the root directory
- Try removing and re-adding the repository

### Add-on Won't Install

- Check Home Assistant logs for errors
- Verify all required files are present (config.yaml, Dockerfile, run.sh)
- Ensure the repository structure is correct
- Check that your architecture is supported (aarch64, amd64, armv7)

### Build Fails

- Check the GitHub Actions tab for build errors
- Verify Dockerfile syntax is correct
- Ensure all dependencies are listed in requirements.txt
- Check that frontend builds successfully

## Updating the Add-on

When you make changes:

```bash
# Make your changes
git add .
git commit -m "Description of changes"

# Update version in config.yaml and CHANGELOG.md
# Then create a new tag
git tag -a v1.0.1 -m "Release version 1.0.1"

# Push changes and tags
git push
git push origin v1.0.1
```

Users will see the update in Home Assistant and can upgrade.

## Sharing Your Add-on

Once your add-on is working:

1. **Home Assistant Community Forum**:
   - Post in the "Share your Projects!" section
   - Include screenshots and description
   - Link to your GitHub repository

2. **Reddit**:
   - Post to r/homeassistant
   - Use flair "Project Showcase"

3. **GitHub Topics**:
   - Add topics to your repository: `home-assistant`, `home-assistant-addon`, `irrigation`

4. **Documentation**:
   - Keep README.md updated
   - Respond to issues promptly
   - Accept pull requests from contributors

## Security Notes

- Never commit sensitive data (tokens, passwords)
- Use Home Assistant's Supervisor API for authentication
- Keep dependencies updated
- Monitor security advisories for your dependencies

## Next Steps

- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Update repository URLs
- [ ] Test installation in Home Assistant
- [ ] Create GitHub release
- [ ] Share with the community
- [ ] Set up issue tracking
- [ ] Monitor for user feedback

## Support

If you encounter issues:
- Check GitHub Actions for build logs
- Review Home Assistant add-on logs
- Search existing GitHub issues
- Create a new issue with details

## Resources

- [Home Assistant Add-on Documentation](https://developers.home-assistant.io/docs/add-ons)
- [Home Assistant Add-on Repository](https://github.com/home-assistant/addons-example)
- [GitHub Documentation](https://docs.github.com)

---

**Current Status**: ✓ Git repository initialized and ready to push

**Next Action**: Create GitHub repository and push code
