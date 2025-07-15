# 🚀 Job Application Agent - Browser Extension Installation Guide

## Quick Setup (5 minutes)

### Step 1: Load Extension in Chrome

1. **Open Chrome Extensions page**
   ```
   chrome://extensions/
   ```

2. **Enable Developer Mode**
   - Toggle the "Developer mode" switch in the top right corner

3. **Load the Extension**
   - Click "Load unpacked" button
   - Navigate to and select the `browser-extension` folder
   - The extension should now appear in your extensions list

### Step 2: Pin the Extension

1. **Click the Extensions puzzle icon** in Chrome toolbar
2. **Find "Job Application Agent"** in the list
3. **Click the pin icon** to pin it to your toolbar

### Step 3: Set Up Your Account

1. **Click the Job Agent extension icon** in your toolbar
2. **Click "Login to Job Agent"** button
3. **Create an account** or login on the web app
4. **Complete your profile** with:
   - Personal information (name, email, phone)
   - Professional links (LinkedIn, portfolio)
   - Resume upload
   - Job preferences

## Testing the Extension

### Try it on a Test Job Application

1. **Visit a job board**:
   - LinkedIn Jobs: https://www.linkedin.com/jobs/
   - Indeed: https://www.indeed.com/
   - Any company careers page

2. **Look for the extension indicators**:
   - Extension badge shows number of forms detected
   - Floating robot icon appears on job application pages
   - Forms get outlined when detected

3. **Use the auto-fill feature**:
   - Click the extension icon
   - Click "Auto-Fill Form" button
   - Watch your information get filled automatically
   - Review and submit the application

## Troubleshooting

### Extension Not Loading
- **Check folder path**: Make sure you selected the `browser-extension` folder (not a parent folder)
- **Check file permissions**: Ensure Chrome can read the files
- **Reload extension**: Go to chrome://extensions/ and click the reload icon

### Forms Not Detected
- **Refresh the page**: Some forms load dynamically
- **Check page compatibility**: Works best on standard job application forms
- **Look for the robot emoji**: Should appear on compatible pages

### Auto-Fill Not Working
- **Login required**: Make sure you're logged in to Job Agent
- **Profile completion**: Ensure your profile has the required information
- **API connection**: Backend must be running on localhost:8000

### Common Issues

**"No job forms found"**
- Wait for page to fully load
- Some forms are hidden until you click "Apply"
- Not all forms are job applications

**"Please login first"**
- Click "Login to Job Agent" in extension popup
- Complete signup/login on web app
- Return to extension and try again

**API connection errors**
- Ensure Job Agent backend is running: http://localhost:8000
- Check that frontend is running: http://localhost:3000
- Verify your internet connection

## Features Overview

### 🔍 Smart Detection
- Automatically scans pages for job application forms
- Works on LinkedIn, Indeed, Glassdoor, and company sites
- Visual indicators show detected forms

### ✨ Auto-Fill Magic
- One-click form filling with your profile data
- Maps personal info, contact details, and professional links
- Handles different form layouts and field names

### 🎯 Intelligent Mapping
**Automatically fills**:
- First Name, Last Name, Full Name
- Email address
- Phone number
- LinkedIn profile URL
- Portfolio/website URL
- Location/address

### 🔐 Secure & Private
- Connects directly to your Job Agent account
- No data stored in the extension
- Secure API communication
- You control all your data

## Supported Websites

**Major Job Boards**:
- ✅ LinkedIn Jobs
- ✅ Indeed
- ✅ Glassdoor
- ✅ Monster
- ✅ Dice
- ✅ Stack Overflow Jobs

**ATS Systems**:
- ✅ Greenhouse
- ✅ Lever
- ✅ Workday
- ✅ BambooHR
- ✅ SmartRecruiters
- ✅ JazzHR
- ✅ Most others!

**Company Career Pages**:
- ✅ Most company websites
- ✅ Custom application forms
- ✅ Dynamic/JavaScript forms

## Advanced Usage

### Context Menu Options
Right-click on any page:
- **"Fill with Job Agent"** - Quick fill for forms
- **"Analyze page for job forms"** - Rescan the page

### Keyboard Shortcuts (Coming Soon)
- `Alt+J` - Open Job Agent popup
- `Alt+F` - Auto-fill detected form
- `Alt+S` - Submit application

### Batch Applications (Coming Soon)
- Apply to multiple jobs in sequence
- Smart queue management
- Success rate tracking

## Privacy & Security

### Data Handling
- ✅ **No tracking**: We don't track your browsing
- ✅ **No storage**: Extension doesn't store personal data
- ✅ **Secure API**: All communication is encrypted
- ✅ **User control**: You manage all your information

### Permissions Explained
- **`activeTab`**: Read current page to detect forms
- **`storage`**: Store login token securely
- **`scripting`**: Inject scripts to fill forms
- **`host_permissions`**: Connect to Job Agent API

## Support

### Getting Help
1. **Check this guide** first for common issues
2. **Look at console logs**: F12 → Console → Look for "Job Agent:" messages
3. **Contact support**: support@jobagent.com
4. **GitHub issues**: Report bugs on our repository

### Debug Mode
Enable detailed logging:
1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for "Job Agent:" prefixed messages
4. Share relevant logs when reporting issues

---

## 🎉 You're All Set!

The Job Application Agent extension is now ready to revolutionize your job search. Start applying to jobs with one click and save hours of repetitive form filling!

## 🔧 Latest Updates (July 2025)

### ✅ Recent Improvements:
- **Enhanced Form Detection**: Improved AI-powered job form recognition with weighted scoring
- **Better Error Handling**: More robust error messages and fallback mechanisms  
- **API Integration**: Complete integration with backend AI services
- **Authentication**: Secure token-based authentication with automatic verification
- **Content Script Optimization**: Better performance and reliability

### 🚀 Current Status:
- ✅ Backend Server: Running on http://localhost:8000
- ✅ Frontend App: Running on http://localhost:3000  
- ✅ All API Endpoints: Functional and tested
- ✅ Form Detection: Enhanced with smart scoring
- ✅ Auto-Fill: Basic and AI-powered modes available
- ✅ Authentication: Secure token verification implemented

### 🧪 Testing the Extension:
1. **Load the extension** in Chrome (Developer mode → Load unpacked)
2. **Visit a job site** like LinkedIn Jobs or Indeed
3. **Look for the extension badge** showing detected forms
4. **Click the extension icon** to see form analysis
5. **Test auto-fill functionality** with your profile data

### 📝 Test Websites:
- LinkedIn Jobs: https://www.linkedin.com/jobs/
- Indeed: https://www.indeed.com/  
- Glassdoor: https://www.glassdoor.com/job-search/
- Any company careers page

**Happy job hunting!** 🎯