// Background service worker for Job Application Agent extension

console.log('Job Agent: Background service worker starting...');

const apiBaseUrl = 'http://localhost:8000';
const formsDetectedTabs = new Set();

// Initialize the service worker
setupEventListeners();
setupContextMenus();

function setupEventListeners() {
  // Listen for tab updates to detect job pages
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
      handleTabUpdate(tabId, tab);
    }
  });

  // Listen for messages from content scripts
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    handleMessage(message, sender, sendResponse);
    return true; // Keep message channel open for async responses
  });

  // Clean up when tabs are closed
  chrome.tabs.onRemoved.addListener((tabId) => {
    formsDetectedTabs.delete(tabId);
  });

  // Handle extension installation
  chrome.runtime.onInstalled.addListener((details) => {
    handleInstallation(details);
  });
}

async function handleTabUpdate(tabId, tab) {
  try {
    // Check if this is a job-related page
    if (isJobRelatedUrl(tab.url)) {
      console.log(`Job Agent: Job-related page detected: ${tab.url}`);
      
      // Update badge to show we're scanning
      chrome.action.setBadgeText({
        tabId: tabId,
        text: '...'
      });
      chrome.action.setBadgeBackgroundColor({
        color: '#ffc107'
      });
    }
  } catch (error) {
    console.error('Error handling tab update:', error);
  }
}

function isJobRelatedUrl(url) {
  if (!url) return false;
  
  const jobSites = [
    'linkedin.com/jobs',
    'indeed.com',
    'glassdoor.com',
    'monster.com',
    'dice.com',
    'stackoverflow.com/jobs',
    'greenhouse.io',
    'lever.co',
    'workday',
    'careers',
    'jobs'
  ];

  return jobSites.some(site => url.toLowerCase().includes(site));
}

function handleMessage(message, sender, sendResponse) {
  switch (message.type) {
    case 'FORMS_DETECTED':
      handleFormsDetected(message, sender);
      sendResponse({ success: true });
      break;
      
    case 'GET_USER_DATA':
      getUserData()
        .then(userData => sendResponse(userData))
        .catch(error => sendResponse({ error: error.message }));
      return true; // Keep message channel open for async response
      
    case 'AUTHENTICATE_USER':
      authenticateUser(message.credentials)
        .then(result => sendResponse(result))
        .catch(error => sendResponse({ error: error.message }));
      return true;
      
    case 'STORE_USER_DATA':
      storeUserData(message.userData)
        .then(() => sendResponse({ success: true }))
        .catch(error => sendResponse({ error: error.message }));
      return true;

    default:
      sendResponse({ error: 'Unknown message type' });
  }
}

function handleFormsDetected(message, sender) {
  const tabId = sender.tab.id;
  formsDetectedTabs.add(tabId);
  
  console.log(`Job Agent: ${message.count} forms detected on tab ${tabId}`);
  
  // Update badge to show form count
  chrome.action.setBadgeText({
    tabId: tabId,
    text: message.count.toString()
  });
  chrome.action.setBadgeBackgroundColor({
    color: '#28a745'
  });
  
  // Store forms data for this tab
  chrome.storage.session.set({
    [`forms_${tabId}`]: message.forms
  });
}

function setupContextMenus() {
  chrome.contextMenus.removeAll(() => {
    // Add context menu for forms
    chrome.contextMenus.create({
      id: 'job-agent-fill-form',
      title: 'Fill with Job Agent',
      contexts: ['editable'],
      documentUrlPatterns: ['http://*/*', 'https://*/*']
    });

    chrome.contextMenus.create({
      id: 'job-agent-analyze-page',
      title: 'Analyze page for job forms',
      contexts: ['page'],
      documentUrlPatterns: ['http://*/*', 'https://*/*']
    });
  });

  // Handle context menu clicks
  chrome.contextMenus.onClicked.addListener((info, tab) => {
    handleContextMenuClick(info, tab);
  });
}

async function handleContextMenuClick(info, tab) {
  switch (info.menuItemId) {
    case 'job-agent-fill-form':
      await fillFormFromContext(tab.id);
      break;
      
    case 'job-agent-analyze-page':
      await analyzePage(tab.id);
      break;
  }
}

async function fillFormFromContext(tabId) {
  try {
    // Get user data
    const userData = await getUserData();
    if (!userData) {
      showNotification('Please login to Job Agent first');
      return;
    }

    // Send message to content script to fill form
    chrome.tabs.sendMessage(tabId, {
      type: 'FILL_CURRENT_FORM',
      userData: userData
    });
  } catch (error) {
    console.error('Error filling form from context:', error);
    showNotification('Error filling form: ' + error.message);
  }
}

async function analyzePage(tabId) {
  try {
    // Send message to content script to reanalyze page
    chrome.tabs.sendMessage(tabId, {
      type: 'REANALYZE_PAGE'
    });
  } catch (error) {
    console.error('Error analyzing page:', error);
  }
}

async function getUserData() {
  try {
    // First check local storage
    const result = await chrome.storage.local.get(['userToken', 'currentUser']);
    
    if (result.userToken && result.currentUser) {
      // Check if token is still valid by making a quick API call
      try {
        const verifyResponse = await apiCall('/api/auth/verify', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${result.userToken}`
          }
        });
        
        if (verifyResponse.ok) {
          return result.currentUser;
        } else {
          // Token invalid, clear storage
          await chrome.storage.local.remove(['userToken', 'currentUser']);
          return null;
        }
      } catch (e) {
        // API unreachable, return cached user data
        return result.currentUser;
      }
    }

    return null;
  } catch (error) {
    console.error('Error getting user data:', error);
    return null;
  }
}

async function authenticateUser(credentials) {
  try {
    const response = await apiCall('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });

    if (response.ok) {
      const authData = await response.json();
      
      // Store auth data
      await chrome.storage.local.set({
        userToken: authData.access_token,
        currentUser: authData.user
      });

      return { success: true, user: authData.user };
    } else {
      const error = await response.json();
      return { success: false, error: error.detail || 'Authentication failed' };
    }
  } catch (error) {
    console.error('Error authenticating user:', error);
    return { success: false, error: error.message };
  }
}

async function storeUserData(userData) {
  await chrome.storage.local.set({
    currentUser: userData,
    lastUpdated: Date.now()
  });
}

async function apiCall(endpoint, options = {}) {
  const url = `${apiBaseUrl}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json'
    }
  };

  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers
    }
  };

  return fetch(url, mergedOptions);
}

function showNotification(message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon-48.png',
    title: 'Job Agent',
    message: message
  });
}

function handleInstallation(details) {
  if (details.reason === 'install') {
    console.log('Job Agent: Extension installed');
    
    // Show welcome notification
    showNotification('Welcome to Job Agent! Click the icon to get started.');
    
    // Open welcome page
    chrome.tabs.create({
      url: 'http://localhost:3000/login'
    });
  } else if (details.reason === 'update') {
    console.log('Job Agent: Extension updated');
  }
}

console.log('Job Agent: Background service worker initialized');