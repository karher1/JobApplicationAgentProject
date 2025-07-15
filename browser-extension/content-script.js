// Content script for Job Application Agent
// This script runs on all web pages to detect and interact with job forms

class JobFormDetector {
  constructor() {
    this.apiBaseUrl = 'http://localhost:8000';
    this.detectedForms = [];
    this.isInitialized = false;
    
    // Only initialize if this looks like a job-related page
    if (this.isJobRelatedPage()) {
      this.init();
    }
  }

  init() {
    if (this.isInitialized) return;
    this.isInitialized = true;
    
    console.log('Job Agent: Initializing on', window.location.hostname);
    
    // Detect forms immediately
    this.detectJobForms();
    
    // Set up observers for dynamic content
    this.setupObservers();
    
    // Listen for messages from popup
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
    });
    
    // Add visual indicators
    this.addVisualIndicators();
  }

  isJobRelatedPage() {
    const url = window.location.href.toLowerCase();
    const content = document.body?.textContent?.toLowerCase() || '';
    
    // Check URL for job-related keywords
    const jobUrlKeywords = [
      'job', 'career', 'apply', 'application', 'position',
      'linkedin.com/jobs', 'indeed.com', 'glassdoor.com',
      'greenhouse.io', 'lever.co', 'workday', 'careers'
    ];
    
    const hasJobUrl = jobUrlKeywords.some(keyword => url.includes(keyword));
    
    // Check page content for job keywords
    const jobContentKeywords = [
      'apply now', 'submit application', 'job application',
      'resume', 'cover letter', 'apply for this position'
    ];
    
    const hasJobContent = jobContentKeywords.some(keyword => content.includes(keyword));
    
    return hasJobUrl || hasJobContent;
  }

  detectJobForms() {
    const forms = Array.from(document.querySelectorAll('form'));
    this.detectedForms = [];

    forms.forEach((form, index) => {
      const formData = this.analyzeForm(form, index);
      if (formData && formData.isJobForm) {
        this.detectedForms.push(formData);
        this.markFormAsDetected(form);
      }
    });

    console.log(`Job Agent: Detected ${this.detectedForms.length} job forms`);
    
    // Notify background script
    if (this.detectedForms.length > 0) {
      chrome.runtime.sendMessage({
        type: 'FORMS_DETECTED',
        count: this.detectedForms.length,
        forms: this.detectedForms
      });
    }
  }

  analyzeForm(form, index) {
    const formText = form.textContent.toLowerCase();
    const formHTML = form.innerHTML.toLowerCase();
    const formAction = form.action.toLowerCase();
    
    // Enhanced job form detection with weighted scoring
    const strongJobIndicators = [
      'submit application', 'apply now', 'job application',
      'upload resume', 'attach cv', 'cover letter', 'apply for this position',
      'submit your application', 'complete application'
    ];

    const jobKeywords = [
      'resume', 'cv', 'application', 'apply', 'job', 'career', 'position',
      'first name', 'last name', 'full name', 'email', 'phone', 'experience',
      'cover letter', 'linkedin', 'portfolio', 'salary', 'availability',
      'work authorization', 'visa status', 'employment', 'hire', 'candidate',
      'qualification', 'skills', 'background', 'education'
    ];

    const antiPatterns = [
      'newsletter', 'subscribe', 'contact us', 'feedback', 'search',
      'login', 'register', 'sign up', 'password', 'forgot password',
      'payment', 'billing', 'checkout', 'cart'
    ];

    // Calculate scores
    let score = 0;
    
    // Strong indicators give high score
    const hasStrongIndicators = strongJobIndicators.some(indicator => {
      if (formText.includes(indicator) || formHTML.includes(indicator) || formAction.includes(indicator)) {
        score += 10;
        return true;
      }
      return false;
    });

    // Count job keywords (weighted)
    const keywordMatches = jobKeywords.filter(keyword =>
      formText.includes(keyword) || formHTML.includes(keyword) || formAction.includes(keyword)
    );
    score += keywordMatches.length * 2;

    // Subtract points for anti-patterns
    const antiPatternMatches = antiPatterns.filter(pattern =>
      formText.includes(pattern) || formHTML.includes(pattern) || formAction.includes(pattern)
    );
    score -= antiPatternMatches.length * 3;

    // Check for file upload inputs (likely resume upload)
    const hasFileInput = form.querySelector('input[type="file"]');
    if (hasFileInput) score += 5;

    // Check for textarea (likely cover letter or essay questions)
    const hasTextarea = form.querySelector('textarea');
    if (hasTextarea) score += 3;

    // Determine if this is a job form (threshold: 5 points)
    const isJobForm = score >= 5;

    if (!isJobForm) return null;

    // Extract form fields
    const fields = this.extractFormFields(form);
    
    // Analyze form complexity and type
    const formType = this.determineFormType(form, fields);
    
    return {
      index: index,
      id: form.id || `job_form_${index}`,
      action: form.action || '',
      method: form.method || 'post',
      isJobForm: true,
      formType: formType,
      confidence: Math.min(score / 20, 1.0), // Normalize score to 0-1
      fields: fields,
      element: form,
      url: window.location.href,
      title: document.title,
      company: this.extractCompanyName(),
      score: score // Include raw score for debugging
    };
  }

  extractFormFields(form) {
    const fields = [];
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach((input, fieldIndex) => {
      // Skip hidden fields, buttons, and checkboxes for now
      if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') {
        return;
      }

      const label = this.findLabelForInput(input);
      const fieldType = this.classifyFieldType(input);
      
      const fieldData = {
        id: input.id || `field_${fieldIndex}`,
        name: input.name || input.id || `field_${fieldIndex}`,
        type: input.type || input.tagName.toLowerCase(),
        label: label,
        placeholder: input.placeholder || '',
        required: input.required || input.hasAttribute('required'),
        value: input.value || '',
        options: this.getSelectOptions(input),
        fieldType: fieldType,
        maxLength: input.maxLength > 0 ? input.maxLength : null,
        isEssayQuestion: fieldType.startsWith('essay') || fieldType === 'coverLetter',
        element: input, // Store reference for AI generation
        context: this.getFieldContext(input, label)
      };

      fields.push(fieldData);
    });

    return fields;
  }

  findLabelForInput(input) {
    // Method 1: Direct label association
    if (input.id) {
      const label = document.querySelector(`label[for="${input.id}"]`);
      if (label) return this.cleanLabelText(label.textContent);
    }
    
    // Method 2: Parent label
    const parentLabel = input.closest('label');
    if (parentLabel) return this.cleanLabelText(parentLabel.textContent);
    
    // Method 3: Sibling elements
    const parent = input.parentElement;
    if (parent) {
      // Look for preceding sibling text
      const prevSibling = input.previousElementSibling;
      if (prevSibling && (prevSibling.tagName === 'LABEL' || prevSibling.tagName === 'SPAN')) {
        return this.cleanLabelText(prevSibling.textContent);
      }
      
      // Look in parent for text content
      const parentText = this.extractTextFromElement(parent, input);
      if (parentText) return parentText;
    }
    
    // Method 4: Use placeholder or name as fallback
    return input.placeholder || this.humanizeFieldName(input.name) || 'Unknown field';
  }

  cleanLabelText(text) {
    return text
      .replace(/[*]/g, '') // Remove asterisks
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  }

  extractTextFromElement(parent, excludeElement) {
    const clone = parent.cloneNode(true);
    
    // Remove the input element and its siblings
    const inputs = clone.querySelectorAll('input, textarea, select, button');
    inputs.forEach(input => input.remove());
    
    const text = clone.textContent.trim();
    if (text.length > 0 && text.length < 100) {
      return this.cleanLabelText(text);
    }
    
    return null;
  }

  humanizeFieldName(name) {
    if (!name) return '';
    
    return name
      .replace(/[_-]/g, ' ') // Replace underscores and hyphens with spaces
      .replace(/([a-z])([A-Z])/g, '$1 $2') // Add space before capital letters
      .toLowerCase()
      .replace(/\b\w/g, l => l.toUpperCase()); // Capitalize first letters
  }

  getSelectOptions(input) {
    if (input.tagName.toLowerCase() !== 'select') return null;
    
    const options = Array.from(input.querySelectorAll('option'))
      .map(option => ({
        value: option.value,
        text: option.textContent.trim()
      }))
      .filter(option => option.value); // Filter out empty options
    
    return options.length > 0 ? options : null;
  }

  classifyFieldType(input) {
    const name = (input.name || '').toLowerCase();
    const label = this.findLabelForInput(input).toLowerCase();
    const placeholder = (input.placeholder || '').toLowerCase();
    
    const fieldText = `${name} ${label} ${placeholder}`;
    
    // Check if this is a textarea for essay questions
    if (input.tagName.toLowerCase() === 'textarea') {
      return this.classifyTextAreaType(fieldText, label);
    }
    
    // Classification mappings for regular fields
    const classifications = {
      'email': ['email', 'e-mail', 'mail'],
      'firstName': ['first name', 'firstname', 'fname', 'given name'],
      'lastName': ['last name', 'lastname', 'lname', 'surname', 'family name'],
      'fullName': ['full name', 'fullname', 'name', 'candidate name'],
      'phone': ['phone', 'telephone', 'mobile', 'cell'],
      'linkedin': ['linkedin', 'linkedin url', 'linkedin profile'],
      'portfolio': ['portfolio', 'website', 'personal website', 'portfolio url'],
      'resume': ['resume', 'cv', 'curriculum vitae', 'upload resume'],
      'coverLetter': ['cover letter', 'covering letter', 'motivation letter'],
      'salary': ['salary', 'compensation', 'expected salary'],
      'availability': ['availability', 'start date', 'available'],
      'experience': ['experience', 'years of experience'],
      'education': ['education', 'degree', 'university', 'school'],
      'location': ['location', 'city', 'address', 'where are you based']
    };

    for (const [type, keywords] of Object.entries(classifications)) {
      if (keywords.some(keyword => fieldText.includes(keyword))) {
        return type;
      }
    }

    return 'other';
  }

  classifyTextAreaType(fieldText, label) {
    // Essay question patterns
    const essayPatterns = {
      'essayMotivation': [
        'why do you want', 'why are you interested', 'what motivates you',
        'why this position', 'why our company', 'what attracts you',
        'why do you wish to work', 'what draws you to'
      ],
      'essayExperience': [
        'tell us about your experience', 'describe your background',
        'what experience do you have', 'relevant experience',
        'describe a time when', 'give an example', 'walk us through'
      ],
      'essayStrengths': [
        'what are your strengths', 'describe your skills',
        'what makes you qualified', 'why should we hire you',
        'what unique value', 'what sets you apart'
      ],
      'essayChallenges': [
        'describe a challenge', 'difficult situation', 'overcome obstacles',
        'problem you solved', 'conflict resolution', 'tell us about a failure'
      ],
      'essayGoals': [
        'career goals', 'where do you see yourself', 'future plans',
        'professional development', 'aspirations', 'long term goals'
      ],
      'essayTeamwork': [
        'team experience', 'collaboration', 'working with others',
        'team project', 'leadership experience', 'describe your teamwork'
      ],
      'essayAboutYou': [
        'tell us about yourself', 'describe yourself',
        'who are you', 'personal statement', 'introduce yourself'
      ],
      'coverLetter': [
        'cover letter', 'covering letter', 'motivation letter',
        'letter of interest', 'why you want to work here'
      ]
    };

    // Check for essay patterns
    for (const [type, keywords] of Object.entries(essayPatterns)) {
      if (keywords.some(keyword => fieldText.includes(keyword))) {
        return type;
      }
    }

    // If it's a large textarea (likely for long responses), classify as general essay
    if (label.length > 10) {
      return 'essayGeneral';
    }

    return 'textArea';
  }

  determineFormType(form, fields) {
    const fieldTypes = fields.map(f => f.fieldType);
    const hasFileUpload = fields.some(f => f.type === 'file');
    const hasTextArea = fields.some(f => f.type === 'textarea');
    
    if (hasFileUpload && (fieldTypes.includes('resume') || fieldTypes.includes('coverLetter'))) {
      return 'full-application';
    } else if (fieldTypes.includes('email') && fieldTypes.includes('firstName')) {
      return 'quick-apply';
    } else if (hasTextArea) {
      return 'detailed-application';
    } else {
      return 'basic-form';
    }
  }

  getFieldContext(input, label) {
    // Gather additional context around the field for AI generation
    const parent = input.parentElement;
    const form = input.closest('form');
    
    // Look for description text near the field
    let description = '';
    if (parent) {
      // Check for help text, descriptions, or hints
      const helpText = parent.querySelector('.help-text, .description, .hint, .field-help');
      if (helpText) {
        description = helpText.textContent.trim();
      }
      
      // Look for sibling text that might be instructions
      const siblings = Array.from(parent.children);
      for (const sibling of siblings) {
        if (sibling !== input && sibling.textContent.length > 20 && sibling.textContent.length < 200) {
          description = sibling.textContent.trim();
          break;
        }
      }
    }
    
    return {
      description: description,
      parentText: parent ? parent.textContent.slice(0, 300) : '',
      formAction: form ? form.action : '',
      pageTitle: document.title,
      pageUrl: window.location.href
    };
  }

  extractCompanyName() {
    // Try to extract company name from page
    const title = document.title;
    const metaTitle = document.querySelector('meta[property="og:title"]')?.content;
    const h1 = document.querySelector('h1')?.textContent;
    
    // Common patterns for company names in job pages
    const patterns = [
      /careers? at (.+?)[\s\-|]/i,
      /(.+?)\s+careers?/i,
      /(.+?)\s+jobs?/i,
      /apply to (.+?)[\s\-|]/i
    ];

    const sources = [title, metaTitle, h1].filter(Boolean);
    
    for (const source of sources) {
      for (const pattern of patterns) {
        const match = source.match(pattern);
        if (match && match[1]) {
          return match[1].trim();
        }
      }
    }

    // Fallback: use domain name
    return window.location.hostname.replace(/^www\./, '').split('.')[0];
  }

  extractJobData() {
    // Extract job information from the current page for AI context
    const title = document.title;
    const company = this.extractCompanyName();
    
    // Look for job description text
    let description = '';
    const descriptionSelectors = [
      '.job-description',
      '.job-details',
      '.position-description',
      '[class*="description"]',
      '.content',
      'main'
    ];
    
    for (const selector of descriptionSelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.length > 100) {
        description = element.textContent.slice(0, 1000); // Limit description length
        break;
      }
    }
    
    // Extract job title from various sources
    let jobTitle = '';
    const titleSelectors = [
      'h1',
      '.job-title',
      '.position-title',
      '[class*="title"]'
    ];
    
    for (const selector of titleSelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim().length > 0) {
        jobTitle = element.textContent.trim();
        break;
      }
    }
    
    // Fallback to extracting from page title
    if (!jobTitle) {
      const titleMatch = title.match(/(.+?)\s*[-|]\s*/);
      jobTitle = titleMatch ? titleMatch[1] : title;
    }
    
    return {
      title: jobTitle,
      company: company,
      description: description,
      url: window.location.href,
      location: this.extractLocation()
    };
  }

  extractLocation() {
    // Try to extract job location from the page
    const locationSelectors = [
      '.location',
      '.job-location',
      '[class*="location"]',
      '.address'
    ];
    
    for (const selector of locationSelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim().length > 0) {
        return element.textContent.trim();
      }
    }
    
    return '';
  }

  setupObservers() {
    // Watch for dynamically added forms
    const observer = new MutationObserver((mutations) => {
      let shouldRecheck = false;
      
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (node.tagName === 'FORM' || node.querySelector('form')) {
              shouldRecheck = true;
            }
          }
        });
      });
      
      if (shouldRecheck) {
        setTimeout(() => this.detectJobForms(), 1000);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  markFormAsDetected(form) {
    // Add visual indicator that form was detected
    form.style.outline = '2px solid #28a745';
    form.style.outlineOffset = '2px';
    
    // Add a small indicator badge
    const indicator = document.createElement('div');
    indicator.innerHTML = '🤖 Job Agent Detected';
    indicator.style.cssText = `
      position: absolute;
      top: -10px;
      right: -10px;
      background: #28a745;
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      z-index: 10000;
      pointer-events: none;
    `;
    
    // Make sure parent has relative positioning
    if (form.parentElement) {
      const parentPosition = getComputedStyle(form.parentElement).position;
      if (parentPosition === 'static') {
        form.parentElement.style.position = 'relative';
      }
      form.parentElement.appendChild(indicator);
    }
  }

  addVisualIndicators() {
    // Add floating action button if forms are detected
    if (this.detectedForms.length > 0) {
      const fab = document.createElement('div');
      fab.innerHTML = '🤖';
      fab.title = 'Job Agent - Auto-fill available';
      fab.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        cursor: pointer;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
      `;
      
      fab.addEventListener('mouseenter', () => {
        fab.style.transform = 'scale(1.1)';
      });
      
      fab.addEventListener('mouseleave', () => {
        fab.style.transform = 'scale(1)';
      });
      
      fab.addEventListener('click', () => {
        // Open extension popup programmatically (if possible)
        alert('Click the Job Agent extension icon to auto-fill this form!');
      });
      
      document.body.appendChild(fab);
    }
  }

  handleMessage(message, sender, sendResponse) {
    switch (message.type) {
      case 'GET_FORMS':
        sendResponse(this.detectedForms);
        break;
        
      case 'REANALYZE_PAGE':
        this.detectJobForms();
        sendResponse({ success: true });
        break;
        
      case 'FILL_FORM':
        this.fillForm(message.formIndex, message.userData)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ error: error.message }));
        return true; // Keep message channel open for async response
        
      case 'FILL_CURRENT_FORM':
        // Fill the first detected form
        if (this.detectedForms.length > 0) {
          this.fillForm(0, message.userData)
            .then(result => sendResponse(result))
            .catch(error => sendResponse({ error: error.message }));
        } else {
          sendResponse({ error: 'No forms detected on this page' });
        }
        return true;
        
      case 'FILL_WITH_AI':
        this.fillFormWithAI(message.formIndex, message.userToken)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ error: error.message }));
        return true;
        
      case 'GENERATE_AI_CONTENT':
        this.generateAIContent(message.fieldId, message.userToken)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ error: error.message }));
        return true;
        
      case 'EXTRACT_JOB_DATA':
        sendResponse({
          success: true,
          jobData: this.extractJobData()
        });
        break;
        
      case 'SUBMIT_FORM':
        this.submitForm(message.formIndex)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ error: error.message }));
        return true;
        
      default:
        sendResponse({ error: 'Unknown message type' });
    }
  }

  async fillForm(formIndex, userData) {
    if (!this.detectedForms[formIndex]) {
      throw new Error('Form not found');
    }

    const formData = this.detectedForms[formIndex];
    const form = document.querySelectorAll('form')[formData.index];
    
    if (!form) {
      throw new Error('Form element not found');
    }

    let filledCount = 0;
    const results = [];

    for (const fieldData of formData.fields) {
      try {
        const field = form.querySelector(`[name="${fieldData.name}"], #${fieldData.id}`);
        if (!field) continue;

        const value = this.mapUserDataToField(fieldData, userData);
        if (value) {
          field.value = value;
          
          // Trigger events to ensure form validation works
          field.dispatchEvent(new Event('input', { bubbles: true }));
          field.dispatchEvent(new Event('change', { bubbles: true }));
          field.dispatchEvent(new Event('blur', { bubbles: true }));
          
          // Visual feedback
          field.style.background = '#d4edda';
          setTimeout(() => {
            field.style.background = '';
          }, 2000);
          
          filledCount++;
          results.push({ field: fieldData.label, value: value, success: true });
        }
      } catch (error) {
        results.push({ field: fieldData.label, error: error.message, success: false });
      }
    }

    return {
      success: true,
      filledCount: filledCount,
      totalFields: formData.fields.length,
      results: results
    };
  }

  mapUserDataToField(fieldData, userData) {
    const mapping = {
      'email': userData.email,
      'firstName': userData.first_name,
      'lastName': userData.last_name,
      'fullName': `${userData.first_name} ${userData.last_name}`.trim(),
      'phone': userData.phone,
      'linkedin': userData.linkedin_url,
      'portfolio': userData.portfolio_url || userData.website_url,
      'location': userData.location
    };

    return mapping[fieldData.fieldType] || '';
  }

  async submitForm(formIndex) {
    if (!this.detectedForms[formIndex]) {
      throw new Error('Form not found');
    }

    const formData = this.detectedForms[formIndex];
    const form = document.querySelectorAll('form')[formData.index];
    
    if (!form) {
      throw new Error('Form element not found');
    }

    // Look for submit button
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]') ||
                        form.querySelector('button:contains("submit"), button:contains("apply")') ||
                        form.querySelector('button');
    
    if (submitButton) {
      submitButton.click();
      return { success: true, method: 'button_click' };
    } else {
      form.submit();
      return { success: true, method: 'form_submit' };
    }
  }

  async fillFormWithAI(formIndex, userToken) {
    if (!this.detectedForms[formIndex]) {
      throw new Error('Form not found');
    }

    const formData = this.detectedForms[formIndex];
    const form = document.querySelectorAll('form')[formData.index];
    
    if (!form) {
      throw new Error('Form element not found');
    }

    const jobData = this.extractJobData();
    let filledCount = 0;
    const results = [];

    // Get user data first from the API
    const userData = await this.getUserData(userToken);
    if (!userData) {
      throw new Error('Could not retrieve user data');
    }

    for (const fieldData of formData.fields) {
      try {
        const field = form.querySelector(`[name="${fieldData.name}"], #${fieldData.id}`);
        if (!field) continue;

        let value = '';

        // Handle regular fields first
        if (!fieldData.isEssayQuestion) {
          value = this.mapUserDataToField(fieldData, userData);
        } else {
          // Generate AI content for essay questions and cover letters
          console.log(`Job Agent: Generating AI content for ${fieldData.fieldType}`);
          
          const aiContent = await this.generateAIContentForField(fieldData, jobData, userData, userToken);
          if (aiContent && aiContent.success) {
            value = aiContent.content;
          }
        }

        if (value) {
          field.value = value;
          
          // Trigger events to ensure form validation works
          field.dispatchEvent(new Event('input', { bubbles: true }));
          field.dispatchEvent(new Event('change', { bubbles: true }));
          field.dispatchEvent(new Event('blur', { bubbles: true }));
          
          // Visual feedback for AI-generated content
          if (fieldData.isEssayQuestion) {
            field.style.background = '#e3f2fd'; // Light blue for AI content
            field.style.border = '2px solid #2196f3';
          } else {
            field.style.background = '#d4edda'; // Green for regular fields
          }
          
          setTimeout(() => {
            field.style.background = '';
            field.style.border = '';
          }, 3000);
          
          filledCount++;
          results.push({ 
            field: fieldData.label, 
            value: value.substring(0, 50) + (value.length > 50 ? '...' : ''),
            type: fieldData.isEssayQuestion ? 'AI-generated' : 'profile-data',
            success: true 
          });
        }
      } catch (error) {
        console.error(`Job Agent: Error filling field ${fieldData.label}:`, error);
        results.push({ field: fieldData.label, error: error.message, success: false });
      }
    }

    return {
      success: true,
      filledCount: filledCount,
      totalFields: formData.fields.length,
      aiGeneratedFields: results.filter(r => r.type === 'AI-generated').length,
      results: results
    };
  }

  async generateAIContent(fieldId, userToken) {
    // Find the field in detected forms
    let targetField = null;
    let formData = null;
    
    for (const form of this.detectedForms) {
      const field = form.fields.find(f => f.id === fieldId);
      if (field) {
        targetField = field;
        formData = form;
        break;
      }
    }
    
    if (!targetField) {
      throw new Error('Field not found');
    }

    if (!targetField.isEssayQuestion) {
      throw new Error('This field does not require AI generation');
    }

    const jobData = this.extractJobData();
    const userData = await this.getUserData(userToken);
    
    return this.generateAIContentForField(targetField, jobData, userData, userToken);
  }

  async generateAIContentForField(fieldData, jobData, userData, userToken) {
    try {
      const endpoint = this.getAIEndpointForFieldType(fieldData.fieldType);
      
      const requestBody = {
        user_id: userData.id,
        job_data: jobData
      };

      // Add field-specific data
      if (fieldData.fieldType === 'coverLetter') {
        requestBody.tone = 'professional';
        requestBody.max_words = Math.min(400, fieldData.maxLength ? fieldData.maxLength / 5 : 400);
      } else if (fieldData.fieldType.startsWith('essay')) {
        requestBody.question = fieldData.label;
        requestBody.field_context = {
          label: fieldData.label,
          field_type: fieldData.type,
          placeholder: fieldData.placeholder,
          max_length: fieldData.maxLength,
          required: fieldData.required
        };
        requestBody.max_words = Math.min(300, fieldData.maxLength ? fieldData.maxLength / 5 : 300);
      } else {
        // Short response
        requestBody.field_label = fieldData.label;
        requestBody.max_words = Math.min(50, fieldData.maxLength ? fieldData.maxLength / 5 : 50);
      }

      const response = await fetch(`${this.apiBaseUrl}/api/ai/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`AI generation failed: ${response.status}`);
      }

      const result = await response.json();
      console.log(`Job Agent: AI content generated for ${fieldData.fieldType}:`, result);
      
      return result;
    } catch (error) {
      console.error('Job Agent: AI generation error:', error);
      throw error;
    }
  }

  getAIEndpointForFieldType(fieldType) {
    if (fieldType === 'coverLetter') {
      return 'generate-cover-letter';
    } else if (fieldType.startsWith('essay')) {
      return 'answer-essay-question';
    } else {
      return 'generate-short-response';
    }
  }

  async getUserData(userToken) {
    try {
      // First get user ID from token verification endpoint
      const verifyResponse = await fetch(`${this.apiBaseUrl}/api/auth/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      });

      if (!verifyResponse.ok) {
        throw new Error('Token verification failed');
      }

      const verifyData = await verifyResponse.json();
      const userId = verifyData.user_id;

      // Get complete user profile
      const profileResponse = await fetch(`${this.apiBaseUrl}/api/users/${userId}/profile`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      });

      if (!profileResponse.ok) {
        throw new Error('Failed to fetch user profile');
      }

      return await profileResponse.json();
    } catch (error) {
      console.error('Job Agent: Error fetching user data:', error);
      return null;
    }
  }
}

// Initialize the form detector
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new JobFormDetector();
  });
} else {
  new JobFormDetector();
}