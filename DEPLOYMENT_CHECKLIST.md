# Deployment Checklist

Use this checklist before deploying the Pro-Irrigation Add-on to production or publishing to a repository.

## Pre-Deployment Verification

### Documentation

- [x] README.md is complete with:
  - [x] Installation instructions
  - [x] Configuration options
  - [x] Usage guide
  - [x] Troubleshooting section
  - [x] API documentation reference

- [x] CHANGELOG.md is created with:
  - [x] Version 1.0.0 documented
  - [x] All features listed
  - [x] Known limitations documented

- [x] INSTALLATION.md provides:
  - [x] Detailed installation steps
  - [x] Testing procedures
  - [x] Verification steps

- [x] LICENSE file is present

- [ ] ICON.md instructions followed (icon.png created)

### Configuration Files

- [x] config.yaml is finalized:
  - [x] Version number set (1.0.0)
  - [x] Correct slug (pro-irrigation)
  - [x] All architectures listed (aarch64, amd64, armv7)
  - [x] Ingress enabled
  - [x] Correct port (8000)
  - [x] Panel icon set (mdi:sprinkler-variant)
  - [x] Options schema defined
  - [x] API access flags set

- [x] Dockerfile is optimized:
  - [x] Multi-stage build implemented
  - [x] Frontend built in separate stage
  - [x] System dependencies installed (gcc, jq)
  - [x] Python dependencies installed
  - [x] Health check configured
  - [x] Environment variables set
  - [x] Proper labels added

- [x] run.sh is functional:
  - [x] Reads Home Assistant options
  - [x] Validates data directory
  - [x] Configurable log level
  - [x] Single worker enforced
  - [x] Proper error handling

- [x] .dockerignore is configured:
  - [x] Excludes unnecessary files
  - [x] Reduces build context size

- [x] repository.json is created

### Build Files

- [x] build.sh script is executable
- [x] Build script supports multiple platforms

## Testing Checklist

### Local Testing

- [ ] Docker build completes successfully:
  ```bash
  ./build.sh
  ```

- [ ] Container runs locally:
  ```bash
  docker run -p 8000:8000 -v $(pwd)/data:/data pro-irrigation:latest
  ```

- [ ] Web interface loads at http://localhost:8000

- [ ] API documentation accessible at http://localhost:8000/api/docs

- [ ] Health check endpoint responds:
  ```bash
  curl http://localhost:8000/api/health
  ```

### Home Assistant Testing

- [ ] Add-on installs successfully in Home Assistant

- [ ] Add-on starts without errors

- [ ] Logs show successful startup

- [ ] Ingress integration works (accessible from sidebar)

- [ ] Database is created at /data/irrigation.db

- [ ] Can create pumps via UI

- [ ] Can create zones via UI

- [ ] Entity discovery works (switches, input helpers)

- [ ] Global settings can be configured

- [ ] Manual mode scheduling works

- [ ] Auto mode scheduling works (with global settings)

- [ ] Pump queue system functions correctly

- [ ] Real-time status updates work

- [ ] Zones execute at scheduled times

- [ ] Pump locks prevent simultaneous execution

### Multi-Architecture Testing

- [ ] Build succeeds for aarch64:
  ```bash
  ./build.sh --platform linux/arm64
  ```

- [ ] Build succeeds for amd64:
  ```bash
  ./build.sh --platform linux/amd64
  ```

- [ ] Build succeeds for armv7:
  ```bash
  ./build.sh --platform linux/arm/v7
  ```

- [ ] Test on actual hardware if available

## Code Quality Checks

### Backend

- [ ] All Python tests pass:
  ```bash
  cd backend && pytest
  ```

- [ ] No linting errors:
  ```bash
  cd backend && pylint **/*.py
  ```

- [ ] Type checking passes (if using mypy):
  ```bash
  cd backend && mypy .
  ```

### Frontend

- [ ] Frontend builds successfully:
  ```bash
  cd frontend && npm run build
  ```

- [ ] No console errors in browser

- [ ] All components render correctly

- [ ] Responsive design works on mobile

## Security Checks

- [ ] No hardcoded credentials or tokens

- [ ] Environment variables used for sensitive data

- [ ] Input validation on all API endpoints

- [ ] SQL injection prevention (SQLAlchemy ORM)

- [ ] XSS protection in frontend

- [ ] CORS properly configured

- [ ] Authentication via Home Assistant Ingress

## Performance Checks

- [ ] API response time < 200ms

- [ ] Frontend loads in < 2 seconds

- [ ] Scheduler cycle completes in < 5 seconds (100 zones)

- [ ] Memory usage < 200MB under normal load

- [ ] No memory leaks during extended operation

## Documentation Review

- [ ] All URLs updated (replace yourusername with actual username)

- [ ] Version numbers consistent across all files

- [ ] Screenshots added to README (if available)

- [ ] API documentation is accurate

- [ ] Troubleshooting section covers common issues

- [ ] Installation instructions tested by someone else

## Repository Preparation

- [ ] Git repository initialized

- [ ] All files committed

- [ ] .gitignore properly configured

- [ ] Tags created for version 1.0.0:
  ```bash
  git tag -a v1.0.0 -m "Release version 1.0.0"
  ```

- [ ] Repository pushed to GitHub/GitLab

- [ ] Repository is public (or accessible to users)

- [ ] Issues enabled on repository

- [ ] README displays correctly on repository page

## Home Assistant Add-on Store

- [ ] Repository URL is correct in repository.json

- [ ] Add-on appears in store after adding repository

- [ ] Add-on metadata displays correctly

- [ ] Icon displays (if icon.png created)

- [ ] Installation from store works

- [ ] Updates work correctly (for future versions)

## Post-Deployment

- [ ] Monitor logs for errors

- [ ] Check for user-reported issues

- [ ] Verify all features work in production

- [ ] Document any issues found

- [ ] Create GitHub issues for bugs

- [ ] Plan next release features

## Optional Enhancements

- [ ] Create demo video or GIF

- [ ] Add screenshots to README

- [ ] Create icon.png (256x256)

- [ ] Set up CI/CD pipeline

- [ ] Add automated testing

- [ ] Create contribution guidelines (CONTRIBUTING.md)

- [ ] Set up issue templates

- [ ] Create pull request template

- [ ] Add code of conduct

- [ ] Set up automated builds for multiple architectures

## Release Announcement

- [ ] Post on Home Assistant Community forum

- [ ] Share on Reddit (r/homeassistant)

- [ ] Tweet about release (if applicable)

- [ ] Update personal website/blog

- [ ] Notify beta testers

## Version Control

Current Version: **1.0.0**

Files to update for version changes:
- config.yaml (version field)
- CHANGELOG.md (new version section)
- Dockerfile (LABEL io.hass.version)
- README.md (if version-specific info)

## Notes

- Keep this checklist updated for future releases
- Add items based on lessons learned
- Document any deployment issues encountered
- Share feedback with development team

## Sign-off

- [ ] All critical items checked
- [ ] All tests passed
- [ ] Documentation reviewed
- [ ] Ready for production deployment

**Deployed by**: _______________  
**Date**: _______________  
**Version**: 1.0.0  
**Notes**: _______________
