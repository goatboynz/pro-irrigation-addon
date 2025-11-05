# GitHub Setup Guide

This guide will help you upload your Pro-Irrigation v2 add-on to GitHub and make it installable in Home Assistant.

## Prerequisites

- Git installed on your computer
- GitHub account
- Your add-on code ready

## Step 1: Create GitHub Repository

1. **Go to GitHub**
   - Navigate to https://github.com
   - Log in to your account

2. **Create New Repository**
   - Click the **+** icon in the top right
   - Select **New repository**
   - Repository name: `pro-irrigation-addon`
   - Description: "Room-based irrigation management system for Home Assistant"
   - Choose **Public** (required for Home Assistant add-on repositories)
   - Do NOT initialize with README (we already have one)
   - Click **Create repository**

## Step 2: Prepare Your Local Repository

1. **Open Terminal/Command Prompt**
   - Navigate to your add-on directory:
     ```bash
     cd /path/to/your/addon
     ```

2. **Initialize Git (if not already done)**
   ```bash
   git init
   ```

3. **Add All Files**
   ```bash
   git add .
   ```

4. **Create Initial Commit**
   ```bash
   git commit -m "Initial commit - Pro-Irrigation v2.0.0"
   ```

## Step 3: Connect to GitHub

1. **Add Remote Repository**
   Replace `YOUR_USERNAME` with your GitHub username:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/pro-irrigation-addon.git
   ```

2. **Verify Remote**
   ```bash
   git remote -v
   ```

3. **Push to GitHub**
   ```bash
   git branch -M main
   git push -u origin main
   ```

## Step 4: Add Repository Images

You need to add icon and logo images for your add-on:

1. **Create Icon (512x512 PNG)**
   - Create or find a sprinkler/irrigation icon
   - Name it `icon.png`
   - Place it in the root directory

2. **Create Logo (256x256 PNG)**
   - Create or find a logo
   - Name it `logo.png`
   - Place it in the root directory

3. **Commit and Push Images**
   ```bash
   git add icon.png logo.png
   git commit -m "Add icon and logo"
   git push
   ```

## Step 5: Create a Release (Optional but Recommended)

Creating releases makes it easier for users to track versions:

1. **Go to Your Repository on GitHub**
   - Navigate to your repository page

2. **Create New Release**
   - Click on **Releases** (right sidebar)
   - Click **Create a new release**
   - Tag version: `v2.0.0`
   - Release title: `Pro-Irrigation v2.0.0 - Initial Release`
   - Description: Copy from CHANGELOG.md
   - Click **Publish release**

## Step 6: Test Installation in Home Assistant

1. **Add Repository to Home Assistant**
   - Open Home Assistant
   - Go to Settings → Add-ons → Add-on Store
   - Click ⋮ (three dots) → Repositories
   - Add: `https://github.com/YOUR_USERNAME/pro-irrigation-addon`
   - Click Add

2. **Install the Add-on**
   - Refresh the Add-on Store
   - Find "Pro-Irrigation v2"
   - Click Install
   - Wait for installation to complete

3. **Start and Test**
   - Start the add-on
   - Check logs for errors
   - Enable "Show in sidebar"
   - Test the interface

## Step 7: Update Repository Information

1. **Update Repository Description**
   - Go to your repository on GitHub
   - Click the ⚙️ icon next to "About"
   - Add description: "Room-based irrigation management system for Home Assistant"
   - Add website: Your documentation URL (if any)
   - Add topics: `home-assistant`, `irrigation`, `home-automation`, `addon`
   - Click "Save changes"

2. **Update README.md**
   - Make sure the GitHub URLs in README.md point to your repository
   - Update any placeholder text

## Step 8: Enable GitHub Actions (Optional)

If you want automated builds:

1. **Go to Repository Settings**
   - Click Settings tab
   - Click Actions → General
   - Enable "Allow all actions and reusable workflows"
   - Click Save

2. **Verify Workflow**
   - Go to Actions tab
   - You should see the "Builder" workflow
   - It will run on every push to main

## Maintenance

### Updating Your Add-on

When you make changes:

1. **Update Version Numbers**
   - Update `config.yaml` version
   - Update `frontend/package.json` version
   - Update `Dockerfile` label
   - Update `CHANGELOG.md`

2. **Commit Changes**
   ```bash
   git add .
   git commit -m "Version 2.1.0 - Description of changes"
   git push
   ```

3. **Create New Release**
   - Go to GitHub → Releases
   - Create new release with new version tag
   - Users will see the update in Home Assistant

### Responding to Issues

1. **Enable Issues**
   - Go to Settings → Features
   - Check "Issues"

2. **Monitor Issues**
   - Check GitHub regularly for user issues
   - Respond promptly
   - Close issues when resolved

### Accepting Contributions

1. **Enable Pull Requests**
   - Already enabled by default

2. **Review Pull Requests**
   - Check code quality
   - Test changes
   - Merge if acceptable

## Troubleshooting

### Push Rejected

If push is rejected:
```bash
git pull origin main --rebase
git push
```

### Authentication Failed

Use a Personal Access Token:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Use token as password when pushing

### Add-on Not Appearing in Home Assistant

1. Verify repository is public
2. Check repository URL is correct
3. Verify `config.yaml` and `repository.json` are correct
4. Try removing and re-adding the repository

### Build Failures

1. Check GitHub Actions logs
2. Verify Dockerfile syntax
3. Test build locally:
   ```bash
   docker build -t test-addon .
   ```

## Best Practices

1. **Use Semantic Versioning**
   - MAJOR.MINOR.PATCH (e.g., 2.0.0)
   - Increment MAJOR for breaking changes
   - Increment MINOR for new features
   - Increment PATCH for bug fixes

2. **Write Good Commit Messages**
   - Use present tense ("Add feature" not "Added feature")
   - Be descriptive but concise
   - Reference issues when applicable

3. **Keep CHANGELOG Updated**
   - Document all changes
   - Organize by version
   - Include dates

4. **Test Before Pushing**
   - Test locally first
   - Verify all features work
   - Check logs for errors

5. **Respond to Community**
   - Answer questions promptly
   - Be friendly and helpful
   - Thank contributors

## Resources

- **Home Assistant Add-on Documentation**: https://developers.home-assistant.io/docs/add-ons
- **GitHub Docs**: https://docs.github.com
- **Git Tutorial**: https://git-scm.com/docs/gittutorial

## Support

If you need help with GitHub setup:
- GitHub Community: https://github.community
- Home Assistant Community: https://community.home-assistant.io

## Next Steps

After setup:
1. Share your repository with the community
2. Consider adding to the Home Assistant Community Add-ons
3. Keep your add-on updated
4. Engage with users
