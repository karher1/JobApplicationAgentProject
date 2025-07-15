// Popup script for Job Application Agent extension
class JobAgentPopup {
  constructor() {
    this.apiBaseUrl = 'http://localhost:8000';
    this.userToken = null;
    this.currentUser = null;
    this.detectedForms = [];
    this.authUtils = new AuthUtils();
    
    this.init();
  }

  async init() {
    console.log('Job Agent popup initializing...');
    
    // Load and verify user authentication
    await this.loadAndVerifyAuth();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Start form detection
    await this.detectJobForms();
    
    // Update UI based on current state
    this.updateUI();
  }

  async loadAndVerifyAuth() {
    try {
      // Use auth utils to verify and refresh authentication
      const authResult = await this.authUtils.verifyAndRefreshAuth();
      
      if (authResult.valid) {
        this.userToken = authResult.token;
        this.currentUser = authResult.user;
        console.log('User authenticated:', this.currentUser?.email);
        
        // Get fresh user profile data
        const freshProfile = await this.authUtils.getUserProfile(this.userToken);
        if (freshProfile) {
          this.currentUser = freshProfile;
          // Update stored user data
          await this.authUtils.storeAuth(this.userToken, freshProfile);
        }
      } else {
        this.userToken = null;
        this.currentUser = null;
        console.log('User not authenticated or token expired');
      }
    } catch (error) {
      console.error('Error loading user authentication:', error);
      this.userToken = null;
      this.currentUser = null;
    }
  }

  setupEventListeners() {
    // Login button
    document.getElementById('login-btn').addEventListener('click', () => {
      chrome.tabs.create({ url: `${this.apiBaseUrl.replace('8000', '3000')}/login` });
    });

    // Auto-fill button
    document.getElementById('fill-btn').addEventListener('click', () => {
      this.fillJobForm();
    });

    // AI Auto-fill button
    document.getElementById('ai-fill-btn').addEventListener('click', () => {
      this.fillJobFormWithAI();
    });

    // Submit button
    document.getElementById('submit-btn').addEventListener('click', () => {
      this.submitApplication();
    });

    // Settings button
    document.getElementById('settings-btn').addEventListener('click', () => {
      chrome.tabs.create({ url: `${this.apiBaseUrl.replace('8000', '3000')}/profile` });
    });
  }

  async detectJobForms() {
    try {
      this.updateStatus('🔍', 'Scanning page...', 'Looking for job application forms');
      
      // Get the current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab) {
        this.updateStatus('❌', 'Error', 'Could not access current tab');
        return;
      }

      // Check if tab URL is accessible
      if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
        this.updateStatus('⚠️', 'Page not accessible', 'Cannot scan Chrome internal pages');
        return;
      }

      try {
        // First try to get forms from content script if already injected
        const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_FORMS' });
        if (response && Array.isArray(response)) {
          this.detectedForms = response;
          this.updateFormsUI();
          return;
        }
      } catch (e) {
        // Content script not loaded, continue with injection
      }

      // Inject content script and detect forms
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: this.detectFormsOnPage
      });

      if (results && results[0] && results[0].result) {
        this.detectedForms = results[0].result;
        console.log('Detected forms:', this.detectedForms);
        this.updateFormsUI();
      } else {
        this.updateStatus('⚠️', 'Scan complete', 'No job application forms detected');
      }
    } catch (error) {
      console.error('Error detecting forms:', error);
      if (error.message.includes('Cannot access')) {
        this.updateStatus('❌', 'Access denied', 'Cannot access this page. Try refreshing or visit a job board.');
      } else {
        this.updateStatus('❌', 'Detection error', 'Failed to scan page for forms');
      }
    }
  }

  updateFormsUI() {
    if (this.detectedForms.length > 0) {
      this.updateStatus('✅', 'Job form detected!', `Found ${this.detectedForms.length} form(s)`);
      this.showFormAnalysis();
      this.showAISection();
    } else {
      this.updateStatus('ℹ️', 'No job forms found', 'This page doesn\'t appear to have job application forms');
    }
  }

  // This function will be injected into the page
  detectFormsOnPage() {
    const forms = Array.from(document.querySelectorAll('form'));
    const jobForms = [];

    forms.forEach((form, index) => {
      // Look for job-related keywords in form and surrounding content
      const formText = form.textContent.toLowerCase();
      const formHTML = form.innerHTML.toLowerCase();
      
      const jobKeywords = [
        'resume', 'cv', 'application', 'apply', 'job', 'career', 'position',
        'first name', 'last name', 'email', 'phone', 'experience',
        'cover letter', 'linkedin', 'portfolio', 'salary'
      ];

      const hasJobKeywords = jobKeywords.some(keyword => 
        formText.includes(keyword) || formHTML.includes(keyword)
      );

      if (hasJobKeywords) {
        // Extract form fields
        const fields = [];
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach((input, fieldIndex) => {
          const label = findLabelForInput(input);
          const fieldType = input.type || input.tagName.toLowerCase();
          
          fields.push({
            id: input.id || `field_${fieldIndex}`,
            name: input.name || input.id || `field_${fieldIndex}`,
            type: fieldType,
            label: label,
            placeholder: input.placeholder || '',
            required: input.required || false,
            value: input.value || ''
          });
        });

        jobForms.push({
          index: index,
          id: form.id || `form_${index}`,
          action: form.action || '',
          method: form.method || 'post',
          fields: fields,
          element: form
        });
      }
    });

    function findLabelForInput(input) {
      // Try to find associated label
      if (input.id) {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label) return label.textContent.trim();
      }
      
      // Look for parent label
      const parentLabel = input.closest('label');
      if (parentLabel) return parentLabel.textContent.trim();
      
      // Look for nearby text
      const parent = input.parentElement;
      if (parent) {
        const text = parent.textContent.replace(input.value, '').trim();
        if (text.length > 0 && text.length < 100) return text;
      }
      
      return input.placeholder || input.name || 'Unknown field';
    }

    return jobForms;
  }

  updateStatus(icon, title, description) {
    document.getElementById('status-icon').textContent = icon;
    document.getElementById('status-title').textContent = title;
    document.getElementById('status-desc').textContent = description;
  }

  showFormAnalysis() {
    const formSection = document.getElementById('form-section');
    const formFields = document.getElementById('form-fields');
    
    if (this.detectedForms.length === 0) {
      formSection.style.display = 'none';
      return;
    }

    // Show first form's fields for now
    const form = this.detectedForms[0];
    formFields.innerHTML = '';

    form.fields.forEach(field => {
      const fieldElement = document.createElement('div');
      fieldElement.className = 'form-field';
      
      const canFill = this.canFillField(field);
      const statusClass = canFill ? 'ready' : 'missing';
      const statusText = canFill ? 'Ready' : 'Missing';
      
      fieldElement.innerHTML = `
        <span class="field-name">${field.label}</span>
        <span class="field-status ${statusClass}">${statusText}</span>
      `;
      
      formFields.appendChild(fieldElement);
    });

    formSection.style.display = 'block';
  }

  canFillField(field) {
    if (!this.currentUser) return false;
    
    const fieldName = field.label.toLowerCase() + ' ' + field.name.toLowerCase();
    
    // Check if we have data for this field
    const dataMap = {
      'first name': this.currentUser.first_name,
      'last name': this.currentUser.last_name,
      'email': this.currentUser.email,
      'phone': this.currentUser.phone,
      'linkedin': this.currentUser.linkedin_url,
      'portfolio': this.currentUser.portfolio_url,
      'website': this.currentUser.website_url
    };

    return Object.keys(dataMap).some(key => {
      return fieldName.includes(key) && dataMap[key];
    });
  }

  async fillJobForm() {
    if (!this.currentUser) {
      alert('Please login first to fill forms');
      return;
    }

    if (this.detectedForms.length === 0) {
      alert('No job forms detected on this page');
      return;
    }

    try {
      document.getElementById('fill-btn').textContent = '⏳ Filling...';
      document.getElementById('fill-btn').disabled = true;

      // Get the current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Fill the form using content script
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: this.fillFormOnPage,
        args: [this.detectedForms[0], this.currentUser]
      });

      this.updateStatus('✅', 'Form filled!', 'Successfully filled job application form');
      
      // Show submit button
      document.getElementById('submit-btn').style.display = 'block';
      
    } catch (error) {
      console.error('Error filling form:', error);
      alert('Error filling form: ' + error.message);
    } finally {
      document.getElementById('fill-btn').textContent = '✨ Auto-Fill Form';
      document.getElementById('fill-btn').disabled = false;
    }
  }

  // Function to be injected into the page for filling
  fillFormOnPage(formData, userData) {
    const form = document.querySelectorAll('form')[formData.index];
    if (!form) return false;

    const fieldMappings = {
      'first name': userData.first_name || '',
      'last name': userData.last_name || '',
      'email': userData.email || '',
      'phone': userData.phone || '',
      'linkedin': userData.linkedin_url || '',
      'portfolio': userData.portfolio_url || '',
      'website': userData.website_url || ''
    };

    let filledCount = 0;

    formData.fields.forEach(fieldInfo => {
      const field = form.querySelector(`[name="${fieldInfo.name}"], #${fieldInfo.id}`);
      if (!field) return;

      const fieldText = (fieldInfo.label + ' ' + fieldInfo.name).toLowerCase();
      
      // Find matching data
      let valueToFill = '';
      for (const [key, value] of Object.entries(fieldMappings)) {
        if (fieldText.includes(key) && value) {
          valueToFill = value;
          break;
        }
      }

      if (valueToFill) {
        field.value = valueToFill;
        field.dispatchEvent(new Event('input', { bubbles: true }));
        field.dispatchEvent(new Event('change', { bubbles: true }));
        filledCount++;
        
        // Add visual feedback
        field.style.background = '#d4edda';
        setTimeout(() => {
          field.style.background = '';
        }, 2000);
      }
    });

    return filledCount;
  }

  async submitApplication() {
    const confirmed = confirm('Are you sure you want to submit this job application?');
    if (!confirmed) return;

    try {
      document.getElementById('submit-btn').textContent = '🚀 Submitting...';
      document.getElementById('submit-btn').disabled = true;

      // Get the current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Submit the form
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: this.submitFormOnPage,
        args: [this.detectedForms[0]]
      });

      this.updateStatus('🎉', 'Application submitted!', 'Your job application has been submitted');
      
    } catch (error) {
      console.error('Error submitting form:', error);
      alert('Error submitting application: ' + error.message);
    } finally {
      document.getElementById('submit-btn').textContent = '🚀 Submit Application';
      document.getElementById('submit-btn').disabled = false;
    }
  }

  // Function to submit form on page
  submitFormOnPage(formData) {
    const form = document.querySelectorAll('form')[formData.index];
    if (!form) return false;

    // Try to find and click submit button
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"], button:contains("submit"), button:contains("apply")');
    
    if (submitButton) {
      submitButton.click();
      return true;
    } else {
      // Fallback: submit the form directly
      form.submit();
      return true;
    }
  }

  updateUI() {
    const userSection = document.getElementById('user-section');
    const loginBtn = document.getElementById('login-btn');
    const fillBtn = document.getElementById('fill-btn');
    const aiFillBtn = document.getElementById('ai-fill-btn');

    if (this.currentUser) {
      // User is logged in
      document.getElementById('user-name').textContent = `${this.currentUser.first_name} ${this.currentUser.last_name}`;
      document.getElementById('user-email').textContent = this.currentUser.email;
      
      userSection.style.display = 'block';
      loginBtn.style.display = 'none';
      
      if (this.detectedForms.length > 0) {
        fillBtn.style.display = 'block';
        aiFillBtn.style.display = 'block';
      }
    } else {
      // User not logged in
      userSection.style.display = 'none';
      loginBtn.style.display = 'block';
      fillBtn.style.display = 'none';
      aiFillBtn.style.display = 'none';
    }
  }

  showAISection() {
    if (this.detectedForms.length === 0) return;

    const aiSection = document.getElementById('ai-section');
    const aiFields = document.getElementById('ai-fields');
    
    // Find AI-capable fields (textareas and cover letter fields)
    const form = this.detectedForms[0];
    const aiCapableFields = form.fields.filter(field => {
      const isTextArea = field.type === 'textarea';
      const isLongText = field.label && field.label.length > 20;
      const hasEssayKeywords = field.label && (
        field.label.toLowerCase().includes('why') ||
        field.label.toLowerCase().includes('describe') ||
        field.label.toLowerCase().includes('tell us') ||
        field.label.toLowerCase().includes('cover letter') ||
        field.label.toLowerCase().includes('motivation')
      );
      
      return isTextArea || (isLongText && hasEssayKeywords);
    });

    if (aiCapableFields.length === 0) {
      aiSection.style.display = 'none';
      return;
    }

    aiFields.innerHTML = '';
    
    aiCapableFields.forEach(field => {
      const fieldElement = document.createElement('div');
      fieldElement.className = 'ai-field';
      
      // Determine field type for styling
      let fieldTypeClass = 'general';
      let fieldTypeText = 'Essay Question';
      
      if (field.label.toLowerCase().includes('cover letter')) {
        fieldTypeClass = 'cover-letter';
        fieldTypeText = 'Cover Letter';
      } else if (field.label.toLowerCase().includes('motivation')) {
        fieldTypeClass = 'essay-question';
        fieldTypeText = 'Motivation';
      } else if (field.label.toLowerCase().includes('experience')) {
        fieldTypeClass = 'essay-question';
        fieldTypeText = 'Experience';
      }
      
      fieldElement.classList.add(fieldTypeClass);
      
      fieldElement.innerHTML = `
        <div class="ai-field-info">
          <div class="ai-field-name">${field.label.substring(0, 30)}${field.label.length > 30 ? '...' : ''}</div>
          <div class="ai-field-type">${fieldTypeText}</div>
        </div>
        <button class="ai-field-btn" data-field-id="${field.id}">Generate</button>
      `;
      
      aiFields.appendChild(fieldElement);
    });

    // Add event listeners for individual field generation
    aiFields.querySelectorAll('.ai-field-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const fieldId = e.target.getAttribute('data-field-id');
        this.generateAIContentForField(fieldId);
      });
    });

    aiSection.style.display = 'block';
  }

  async fillJobFormWithAI() {
    if (!this.currentUser || !this.userToken) {
      alert('Please login first to use AI features');
      return;
    }

    if (this.detectedForms.length === 0) {
      alert('No job forms detected on this page');
      return;
    }

    try {
      const aiFillBtn = document.getElementById('ai-fill-btn');
      aiFillBtn.textContent = '🤖 AI Filling...';
      aiFillBtn.disabled = true;

      // Get the current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Send message to content script to fill with AI
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: 'FILL_WITH_AI',
        formIndex: 0,
        userToken: this.userToken
      });

      if (response && response.success) {
        this.updateStatus('✅', 'AI Form filled!', 
          `Filled ${response.filledCount}/${response.totalFields} fields (${response.aiGeneratedFields} AI-generated)`);
        
        // Show submit button
        document.getElementById('submit-btn').style.display = 'block';
      } else {
        throw new Error(response?.error || 'AI fill failed');
      }
      
    } catch (error) {
      console.error('Error with AI filling:', error);
      alert('Error with AI filling: ' + error.message);
    } finally {
      const aiFillBtn = document.getElementById('ai-fill-btn');
      aiFillBtn.textContent = '🤖 AI Auto-Fill';
      aiFillBtn.disabled = false;
    }
  }

  async generateAIContentForField(fieldId) {
    if (!this.currentUser || !this.userToken) {
      alert('Please login first to use AI features');
      return;
    }

    try {
      const fieldBtn = document.querySelector(`[data-field-id="${fieldId}"]`);
      const fieldElement = fieldBtn.closest('.ai-field');
      
      fieldBtn.textContent = 'Generating...';
      fieldBtn.disabled = true;
      fieldElement.classList.add('ai-generating');

      // Get the current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Send message to content script to generate AI content for specific field
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: 'GENERATE_AI_CONTENT',
        fieldId: fieldId,
        userToken: this.userToken
      });

      if (response && response.success) {
        fieldBtn.textContent = 'Generated ✓';
        fieldElement.classList.remove('ai-generating');
        
        // Update status
        this.updateStatus('✅', 'AI Content Generated', 
          `Generated ${response.word_count} words for ${response.question_type || 'field'}`);
      } else {
        throw new Error(response?.error || 'AI generation failed');
      }
      
    } catch (error) {
      console.error('Error generating AI content:', error);
      alert('Error generating AI content: ' + error.message);
    } finally {
      const fieldBtn = document.querySelector(`[data-field-id="${fieldId}"]`);
      const fieldElement = fieldBtn.closest('.ai-field');
      
      if (fieldBtn.textContent !== 'Generated ✓') {
        fieldBtn.textContent = 'Generate';
      }
      fieldBtn.disabled = false;
      fieldElement.classList.remove('ai-generating');
    }
  }
}

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', () => {
  new JobAgentPopup();
});