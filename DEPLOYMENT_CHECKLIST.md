# Deployment Checklist

Use this checklist to ensure everything is ready before deploying to GitHub and Home Assistant.

## Pre-Deployment Checks

### Code Quality
- [ ] All features implemented and tested
- [ ] No console.log or debug statements in production code
- [ ] Error handling implemented for all API calls
- [ ] Database migrations tested
- [ ] Frontend builds without errors (`npm run build`)
- [ ] Backend starts without errors

### Documentation
- [ ] README.md is complete and accurate
- [ ] INSTALL.md has clear installation instructions
- [ ] CHANGELOG.md is up to date
- [ ] API documentation is complete (check /docs endpoint)
- [ ] Code comments are clear and helpful

### Configuration Files
- [ ] config.yaml has correct version number
- [ ] config.yaml has correct repository URL
- [ ] Dockerfile builds successfully
- [ ] run.sh is executable and works
- [ ] requirements.txt has all dependencies
- [ ] package.json has correct version

### Assets
- [ ] icon.png exists (512x512 PNG)
- [ ] logo.png exists (256x256 PNG)
- [ ] Images are optimized for web
- [ ] No placeholder images remain

### Version Numbers
- [ ] config.yaml version: 2.0.0
- [ ] frontend/package.json version: 2.0.0
- [ ] Dockerfile label version: 2.0.0
- [ ] CHANGELOG.md has entry for 2.0.0
- [ ] All version numbers match

### Security
- [ ] No hardcoded credentials
- [ ] No API keys in code
- [ ] .gitignore excludes sensitive files
- [ ] Database files excluded from git
- [ ] Environment variables used for secrets

### Testing
- [ ] Manual testing completed
- [ ] All CRUD operations work
- [ ] Scheduler runs correctly
- [ ] Queue processor works
- [ ] Manual control functions
- [ ] Sensor data retrieval works
- [ ] Settings can be updated
- [ ] System reset works

## GitHub Setup

### Repository Creation
- [ ] GitHub account ready
- [ ] Repository created: pro-irrigation-addon
- [ ] Repository is PUBLIC
- [ ] Repository description added
- [ ] Topics added (home-assistant, irrigation, etc.)

### Initial Commit
- [ ] Git initialized
- [ ] All files added to git
- [ ] Initial commit created
- [ ] Remote repository configured
- [ ] Code pushed to GitHub

### Repository Configuration
- [ ] README.md displays correctly on GitHub
- [ ] LICENSE file is present
- [ ] .gitignore is working
- [ ] GitHub Actions enabled (optional)
- [ ] Issues enabled
- [ ] Discussions enabled (optional)

### Release Creation
- [ ] First release created (v2.0.0)
- [ ] Release notes from CHANGELOG
- [ ] Release tagged correctly
- [ ] Release published

## Home Assistant Testing

### Installation
- [ ] Repository added to Home Assistant
- [ ] Add-on appears in store
- [ ] Add-on installs successfully
- [ ] Add-on starts without errors
- [ ] Logs show "Startup complete"

### Functionality
- [ ] Web interface loads
- [ ] Can create rooms
- [ ] Can create pumps
- [ ] Can create zones
- [ ] Can create water events
- [ ] Can add sensors
- [ ] Manual control works
- [ ] Settings can be changed

### Integration
- [ ] Can discover Home Assistant entities
- [ ] Can control switches
- [ ] Can read sensor values
- [ ] Can query entity states
- [ ] Ingress works correctly
- [ ] Sidebar integration works

### Performance
- [ ] Frontend loads quickly (< 2 seconds)
- [ ] API responses are fast (< 200ms)
- [ ] Scheduler runs on time
- [ ] Queue processor is responsive
- [ ] No memory leaks
- [ ] CPU usage is reasonable

## Post-Deployment

### Documentation
- [ ] Update README with actual GitHub URL
- [ ] Add screenshots to README
- [ ] Create wiki pages (optional)
- [ ] Write blog post (optional)

### Community
- [ ] Post to Home Assistant Community forum
- [ ] Share on Reddit r/homeassistant
- [ ] Tweet about release (optional)
- [ ] Add to awesome-home-assistant list

### Monitoring
- [ ] Watch for GitHub issues
- [ ] Monitor discussions
- [ ] Check for pull requests
- [ ] Review user feedback

### Maintenance
- [ ] Set up issue templates
- [ ] Create contributing guidelines
- [ ] Plan next version features
- [ ] Schedule regular updates

## Troubleshooting Common Issues

### Build Fails
- Check Dockerfile syntax
- Verify all dependencies are listed
- Test build locally: `docker build -t test .`
- Check GitHub Actions logs

### Add-on Won't Install
- Verify repository is public
- Check config.yaml syntax
- Ensure all required files exist
- Check Home Assistant logs

### Frontend Not Loading
- Verify frontend built correctly
- Check static files are in dist/
- Verify Dockerfile copies dist/
- Check browser console for errors

### API Errors
- Check backend logs
- Verify database is accessible
- Check Home Assistant API token
- Test endpoints with curl

### Scheduler Not Running
- Check scheduler logs
- Verify events are configured
- Check room/event enabled status
- Verify entity IDs are correct

## Final Verification

Before announcing your add-on:

1. **Fresh Install Test**
   - Remove add-on completely
   - Re-add repository
   - Install from scratch
   - Verify everything works

2. **Documentation Review**
   - Read through all docs as a new user
   - Verify all links work
   - Check for typos
   - Ensure clarity

3. **Community Readiness**
   - Prepare to answer questions
   - Have troubleshooting guide ready
   - Be responsive to issues
   - Thank early adopters

## Success Criteria

Your add-on is ready when:

- ✅ All checklist items are complete
- ✅ Fresh install works perfectly
- ✅ Documentation is clear and complete
- ✅ No critical bugs remain
- ✅ You're ready to support users

## Notes

- Keep this checklist updated as you add features
- Use it for every release
- Share with contributors
- Adapt to your workflow

## Resources

- Home Assistant Add-on Docs: https://developers.home-assistant.io/docs/add-ons
- GitHub Docs: https://docs.github.com
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/

---

**Remember**: It's better to delay release and get it right than to rush and have a poor user experience.

Good luck with your deployment! 🚀
