#!/bin/bash

# Pro-Irrigation v2 - GitHub Setup Script
# This script helps you quickly set up your repository on GitHub

set -e

echo "============================================================"
echo "Pro-Irrigation v2 - GitHub Setup Helper"
echo "============================================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed. Please install Git first."
    echo "Visit: https://git-scm.com/downloads"
    exit 1
fi

echo "Git is installed ✓"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    echo "Git repository initialized ✓"
else
    echo "Git repository already exists ✓"
fi

echo ""
echo "============================================================"
echo "GitHub Repository Setup"
echo "============================================================"
echo ""
echo "Before continuing, please:"
echo "1. Create a new repository on GitHub"
echo "2. Name it: pro-irrigation-addon"
echo "3. Make it PUBLIC (required for Home Assistant)"
echo "4. Do NOT initialize with README"
echo ""
read -p "Have you created the GitHub repository? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please create the repository first, then run this script again."
    exit 1
fi

echo ""
read -p "Enter your GitHub username: " github_username

if [ -z "$github_username" ]; then
    echo "ERROR: GitHub username cannot be empty"
    exit 1
fi

echo ""
echo "Setting up remote repository..."

# Check if remote already exists
if git remote | grep -q "origin"; then
    echo "Remote 'origin' already exists. Updating URL..."
    git remote set-url origin "https://github.com/$github_username/pro-irrigation-addon.git"
else
    git remote add origin "https://github.com/$github_username/pro-irrigation-addon.git"
fi

echo "Remote repository configured ✓"
echo ""

# Check if there are any commits
if ! git rev-parse HEAD &> /dev/null; then
    echo "Creating initial commit..."
    git add .
    git commit -m "Initial commit - Pro-Irrigation v2.0.0"
    echo "Initial commit created ✓"
else
    echo "Commits already exist ✓"
fi

echo ""
echo "============================================================"
echo "Ready to Push"
echo "============================================================"
echo ""
echo "Your repository is configured:"
echo "  Remote: https://github.com/$github_username/pro-irrigation-addon.git"
echo ""
read -p "Push to GitHub now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Pushing to GitHub..."
    git branch -M main
    git push -u origin main
    echo ""
    echo "============================================================"
    echo "Success!"
    echo "============================================================"
    echo ""
    echo "Your add-on is now on GitHub!"
    echo ""
    echo "Next steps:"
    echo "1. Add icon.png and logo.png images to your repository"
    echo "2. Visit: https://github.com/$github_username/pro-irrigation-addon"
    echo "3. Create a release (optional but recommended)"
    echo "4. Add to Home Assistant:"
    echo "   https://github.com/$github_username/pro-irrigation-addon"
    echo ""
    echo "See INSTALL.md for installation instructions"
    echo "See GITHUB_SETUP.md for detailed GitHub setup guide"
    echo ""
else
    echo ""
    echo "Skipped push. You can push manually later with:"
    echo "  git push -u origin main"
    echo ""
fi

echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
