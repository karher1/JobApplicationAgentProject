# Job Application Agent - Browser Extension

🚀 **Automatically detect and fill job application forms with one click!**

## Features

- 🔍 **Smart Form Detection** - Automatically detects job application forms on any website
- ✨ **One-Click Auto-Fill** - Fills forms with your profile data instantly
- 🤖 **AI-Powered Field Mapping** - Intelligently maps your data to form fields
- 🎯 **Works Everywhere** - LinkedIn, Indeed, Glassdoor, company career pages, and more
- 🔐 **Secure** - Connects securely to your Job Application Agent account
- 📱 **Visual Feedback** - Clear indicators showing detected forms and fill status

## Installation

### For Development

1. **Clone the repository** (if not already done):
   ```bash
   git clone <your-repo-url>
   cd JobApplicationAgent/browser-extension
   ```

2. **Load the extension in Chrome**:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `browser-extension` folder

3. **Set up your Job Agent account**:
   - Make sure the Job Application Agent backend is running on `http://localhost:8000`
   - Make sure the frontend is running on `http://localhost:3000`
   - Create an account or login via the extension popup

## How to Use

1. **Login to your account** via the extension popup
2. **Visit any job application page** (LinkedIn, Indeed, company sites, etc.)
3. **Click the extension icon** - it will show detected forms
4. **Click "Auto-Fill Form"** to instantly fill the application
5. **Review and submit** your application

## Supported Websites

The extension works on most job application websites including:

- **LinkedIn Jobs** - Apply with LinkedIn, external applications
- **Indeed** - Direct applications and redirected forms
- **Glassdoor** - Company applications
- **Company Career Pages** - Most ATS systems including:
  - Greenhouse
  - Lever
  - Workday
  - BambooHR
  - SmartRecruiters
  - And many more!

## Features in Detail

### 🔍 Smart Detection
- Automatically scans pages for job application forms
- Uses AI to identify relevant form fields
- Works with dynamic/JavaScript-loaded forms
- Visual indicators show when forms are detected

### ✨ Auto-Fill Magic
- Maps your profile data to the correct form fields
- Handles different field naming conventions
- Supports text inputs, dropdowns, textareas
- Triggers proper form validation events

### 🎯 Field Mapping
The extension automatically fills:
- **Personal Info**: Name, email, phone, location
- **Professional**: LinkedIn profile, portfolio website
- **Files**: Resume upload (coming soon)
- **Custom Fields**: Based on your profile data

### 🔐 Security
- All data is encrypted and secure
- No data is stored in the extension itself
- Connects directly to your Job Agent backend
- You maintain full control of your data

## Technical Details

### Architecture
- **Manifest V3** - Latest Chrome extension standard
- **Content Scripts** - For form detection and interaction
- **Service Worker** - Background processing and API calls
- **Popup Interface** - User interaction and status display

### API Integration
The extension connects to your Job Application Agent backend:
- Authentication via JWT tokens
- User profile data retrieval
- Form submission tracking
- Secure communication over HTTPS (in production)

### Browser Compatibility
- ✅ **Chrome** (Primary support)
- ✅ **Edge** (Chromium-based)
- 🔄 **Firefox** (Coming soon)
- 🔄 **Safari** (Planned)

## Development

### File Structure
```
browser-extension/
├── manifest.json          # Extension configuration
├── popup.html             # Extension popup interface
├── popup.css              # Popup styling
├── popup.js               # Popup logic
├── content-script.js      # Page interaction logic
├── content-styles.css     # Content script styles
├── background.js          # Service worker
├── icons/                 # Extension icons
└── README.md              # This file
```

### Key Components

1. **Content Script** (`content-script.js`)
   - Runs on all web pages
   - Detects job application forms
   - Handles form filling and submission
   - Provides visual feedback

2. **Popup Interface** (`popup.html/js/css`)
   - User interface when clicking extension icon
   - Shows detection status and user info
   - Provides auto-fill and submit buttons

3. **Background Service Worker** (`background.js`)
   - Handles API communication
   - Manages user authentication
   - Coordinates between popup and content scripts

### Adding New Field Types

To add support for new form field types:

1. **Update field classification** in `content-script.js`:
   ```javascript
   const classifications = {
     'newFieldType': ['keyword1', 'keyword2', 'keyword3']
   };
   ```

2. **Add data mapping** in the `mapUserDataToField` function:
   ```javascript
   const mapping = {
     'newFieldType': userData.new_field_value
   };
   ```

3. **Test on relevant websites** to ensure proper detection

## Troubleshooting

### Common Issues

**Extension not detecting forms:**
- Refresh the page and try again
- Check if the page loaded completely
- Some forms load dynamically - wait a few seconds

**Auto-fill not working:**
- Make sure you're logged in to Job Agent
- Check that your profile has the required data
- Try refreshing both the page and your login

**API connection errors:**
- Ensure the Job Agent backend is running on localhost:8000
- Check your internet connection
- Try logging out and back in

### Debug Mode

To enable debug logging:
1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Look for "Job Agent:" prefixed messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on multiple job sites
5. Submit a pull request

## Roadmap

### Near Term
- [ ] Firefox support
- [ ] File upload handling (resume/cover letter)
- [ ] Form submission confirmation
- [ ] Better error handling and user feedback

### Future Features
- [ ] AI-powered cover letter generation
- [ ] Application tracking integration
- [ ] A/B testing for different application strategies
- [ ] Mobile browser support
- [ ] Enterprise SSO integration

## Privacy & Security

- ✅ No data tracking or analytics
- ✅ All data stays within your Job Agent account
- ✅ Secure API communication
- ✅ No third-party data sharing
- ✅ Open source and auditable

## Support

For issues or questions:
1. Check this README first
2. Look at the console logs for errors
3. Report issues on GitHub
4. Contact the Job Agent support team

---

**Happy job hunting! 🎯**