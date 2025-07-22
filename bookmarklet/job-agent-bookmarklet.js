/**
 * Job Application Agent - Bookmarklet
 * One-click job application auto-fill for any website
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    apiBaseUrl: 'http://localhost:8000',
    frontendUrl: 'http://localhost:3000',
    version: '1.0.0'
  };

  // User data - will be fetched from backend
  let userData = null;
  let userToken = null;

  // Main JobAgent class
  class JobAgent {
    constructor() {
      this.detectedForms = [];
      this.isVisible = false;
      this.ui = null;
      this.init();
    }

    async init() {
      console.log('🤖 Job Agent Bookmarklet v' + CONFIG.version + ' starting...');
      
      // Check if already running
      if (window.jobAgentBookmarklet) {
        console.log('Job Agent already running, toggling UI...');
        window.jobAgentBookmarklet.toggleUI();
        return;
      }

      // Set global reference
      window.jobAgentBookmarklet = this;

      try {
        // Load user authentication
        await this.loadAuth();
        
        // Detect job forms
        this.detectJobForms();
        
        // Create and show UI
        this.createUI();
        
        console.log(`🎯 Found ${this.detectedForms.length} job application forms`);
        
      } catch (error) {
        console.error('Job Agent initialization error:', error);
        this.showError('Failed to initialize Job Agent: ' + error.message);
      }
    }

    async loadAuth() {
      // Try to get auth from localStorage (if on frontend domain)
      if (window.location.hostname === 'localhost' && window.location.port === '3000') {
        const authToken = localStorage.getItem('auth_token');
        if (authToken) {
          try {
            const authData = JSON.parse(authToken);
            userToken = authData.access_token;
            userData = authData.user;
            console.log('✅ Loaded auth from frontend localStorage');
            return;
          } catch (e) {
            console.log('Could not parse auth_token from localStorage');
          }
        }
      }

      // Try to fetch from backend using test credentials
      try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            email: 'jane@email.com',
            password: 'testpass123'
          })
        });

        if (response.ok) {
          const authData = await response.json();
          userToken = authData.access_token;
          userData = authData.user;
          console.log('✅ Authenticated with backend');
        } else {
          throw new Error('Authentication failed');
        }
      } catch (error) {
        console.warn('Could not authenticate:', error.message);
        // Use demo data as fallback
        userData = {
          email: 'jane@email.com',
          first_name: 'Jane',
          last_name: 'Doe',
          phone: '+1 (555) 123-4567',
          linkedin_url: 'https://linkedin.com/in/janedoe',
          portfolio_url: 'https://janedoe.dev',
          location: 'San Francisco, CA'
        };
        console.log('🔄 Using demo user data');
      }
    }

    detectJobForms() {
      this.detectedForms = [];

      // Look for forms first
      const forms = document.querySelectorAll('form');
      forms.forEach((form, index) => {
        const formData = this.analyzeForm(form, index);
        if (formData && formData.isJobForm) {
          this.detectedForms.push(formData);
        }
      });

      // If no forms found, look for standalone input fields (SPA pattern)
      if (this.detectedForms.length === 0) {
        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], textarea, select');
        if (inputs.length > 3) {
          const virtualForm = this.createVirtualForm(inputs);
          if (virtualForm) {
            this.detectedForms.push(virtualForm);
          }
        }
      }
    }

    analyzeForm(form, index) {
      const formText = form.textContent.toLowerCase();
      const formHTML = form.innerHTML.toLowerCase();
      
      // Job form indicators
      const jobKeywords = [
        'resume', 'cv', 'application', 'apply', 'job', 'career', 'position',
        'first name', 'last name', 'email', 'phone', 'experience',
        'cover letter', 'linkedin', 'portfolio', 'salary'
      ];

      const score = jobKeywords.filter(keyword => 
        formText.includes(keyword) || formHTML.includes(keyword)
      ).length;

      // Must have at least 3 job-related keywords
      if (score < 3) return null;

      const fields = this.extractFormFields(form);
      
      return {
        index: index,
        id: form.id || `job_form_${index}`,
        element: form,
        fields: fields,
        isJobForm: true,
        confidence: Math.min(score / 10, 1.0),
        title: document.title,
        url: window.location.href
      };
    }

    createVirtualForm(inputs) {
      const fields = [];
      
      Array.from(inputs).forEach((input, index) => {
        const field = this.analyzeField(input, index);
        if (field) {
          fields.push(field);
        }
      });

      if (fields.length < 3) return null;

      return {
        index: 0,
        id: 'virtual_spa_form',
        element: document.body,
        fields: fields,
        isJobForm: true,
        confidence: 0.8,
        title: document.title,
        url: window.location.href,
        isVirtual: true
      };
    }

    extractFormFields(form) {
      const fields = [];
      const inputs = form.querySelectorAll('input, textarea, select');
      
      inputs.forEach((input, index) => {
        if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') {
          return;
        }

        const field = this.analyzeField(input, index);
        if (field) {
          fields.push(field);
        }
      });

      return fields;
    }

    analyzeField(input, index) {
      const label = this.findLabelForInput(input);
      const fieldType = this.classifyFieldType(input, label);
      
      return {
        id: input.id || `field_${index}`,
        name: input.name || input.id || `field_${index}`,
        type: input.type || input.tagName.toLowerCase(),
        label: label,
        placeholder: input.placeholder || '',
        required: input.required,
        element: input,
        fieldType: fieldType,
        isEssayQuestion: fieldType.startsWith('essay') || fieldType === 'coverLetter'
      };
    }

    findLabelForInput(input) {
      // Method 1: Direct label association
      if (input.id) {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label) return label.textContent.trim();
      }
      
      // Method 2: Parent label
      const parentLabel = input.closest('label');
      if (parentLabel) return parentLabel.textContent.trim();
      
      // Method 3: Previous sibling
      const prevSibling = input.previousElementSibling;
      if (prevSibling && (prevSibling.tagName === 'LABEL' || prevSibling.tagName === 'SPAN')) {
        return prevSibling.textContent.trim();
      }
      
      // Method 4: Use placeholder or name
      return input.placeholder || this.humanizeFieldName(input.name) || 'Unknown field';
    }

    classifyFieldType(input, label) {
      const text = `${input.name} ${label} ${input.placeholder}`.toLowerCase();
      
      const classifications = {
        'email': ['email', 'e-mail'],
        'firstName': ['first name', 'firstname', 'fname', 'given name'],
        'lastName': ['last name', 'lastname', 'lname', 'surname'],
        'fullName': ['full name', 'fullname', 'name'],
        'phone': ['phone', 'telephone', 'mobile', 'cell'],
        'linkedin': ['linkedin', 'linkedin url'],
        'portfolio': ['portfolio', 'website', 'personal website'],
        'location': ['location', 'city', 'address'],
        'coverLetter': ['cover letter', 'covering letter'],
        'resume': ['resume', 'cv', 'curriculum vitae']
      };

      for (const [type, keywords] of Object.entries(classifications)) {
        if (keywords.some(keyword => text.includes(keyword))) {
          return type;
        }
      }

      // Check for essay questions in textareas
      if (input.tagName.toLowerCase() === 'textarea') {
        const essayKeywords = [
          'why do you want', 'tell us about', 'describe your',
          'what motivates you', 'why are you interested'
        ];
        
        if (essayKeywords.some(keyword => text.includes(keyword))) {
          return 'essayGeneral';
        }
        return 'coverLetter';
      }

      return 'other';
    }

    humanizeFieldName(name) {
      if (!name) return '';
      return name
        .replace(/[_-]/g, ' ')
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .toLowerCase()
        .replace(/\b\w/g, l => l.toUpperCase());
    }

    async fillForm(formIndex = 0) {
      if (!this.detectedForms[formIndex]) {
        this.showError('No form found to fill');
        return;
      }

      if (!userData) {
        this.showError('User data not available');
        return;
      }

      const form = this.detectedForms[formIndex];
      let filledCount = 0;

      console.log('🔄 Filling form with', form.fields.length, 'fields...');

      for (const field of form.fields) {
        const value = this.mapUserDataToField(field);
        if (value && field.element) {
          try {
            // Set the value
            field.element.value = value;
            
            // Trigger events for React/Vue/Angular forms
            field.element.dispatchEvent(new Event('input', { bubbles: true }));
            field.element.dispatchEvent(new Event('change', { bubbles: true }));
            field.element.dispatchEvent(new Event('blur', { bubbles: true }));
            
            // Visual feedback
            this.highlightField(field.element, 'success');
            
            filledCount++;
          } catch (error) {
            console.warn('Error filling field:', field.label, error);
            this.highlightField(field.element, 'error');
          }
        }
      }

      this.showSuccess(`Filled ${filledCount} out of ${form.fields.length} fields`);
      this.updateUI();
    }

    mapUserDataToField(field) {
      if (!userData) return '';

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

      return mapping[field.fieldType] || '';
    }

    async generateAIContent(field) {
      if (!userToken) {
        this.showError('Authentication required for AI features');
        return;
      }

      try {
        const endpoint = field.fieldType === 'coverLetter' ? 
          'generate-cover-letter' : 
          'answer-essay-question';

        const response = await fetch(`${CONFIG.apiBaseUrl}/api/ai/${endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userToken}`
          },
          body: JSON.stringify({
            user_id: userData.id,
            job_data: {
              title: document.title,
              company: this.extractCompanyName(),
              url: window.location.href
            },
            question: field.label,
            field_context: {
              label: field.label,
              placeholder: field.placeholder,
              max_length: field.element.maxLength
            }
          })
        });

        if (!response.ok) {
          throw new Error(`AI generation failed: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success && result.content) {
          field.element.value = result.content;
          field.element.dispatchEvent(new Event('input', { bubbles: true }));
          this.highlightField(field.element, 'ai');
          this.showSuccess('AI content generated successfully');
        }

      } catch (error) {
        console.error('AI generation error:', error);
        this.showError('AI generation failed: ' + error.message);
      }
    }

    extractCompanyName() {
      const title = document.title;
      const h1 = document.querySelector('h1')?.textContent;
      
      const patterns = [
        /careers? at (.+?)[\s\-|]/i,
        /(.+?)\s+careers?/i,
        /(.+?)\s+jobs?/i
      ];

      const sources = [title, h1].filter(Boolean);
      
      for (const source of sources) {
        for (const pattern of patterns) {
          const match = source.match(pattern);
          if (match && match[1]) {
            return match[1].trim();
          }
        }
      }

      return window.location.hostname.replace(/^www\./, '').split('.')[0];
    }

    highlightField(element, type) {
      const colors = {
        'success': '#d4edda',
        'error': '#f8d7da',
        'ai': '#e3f2fd'
      };
      
      element.style.backgroundColor = colors[type];
      element.style.transition = 'background-color 0.3s ease';
      
      setTimeout(() => {
        element.style.backgroundColor = '';
      }, 2000);
    }

    createUI() {
      // Remove existing UI
      const existing = document.getElementById('job-agent-ui');
      if (existing) existing.remove();

      // Create main UI container
      this.ui = document.createElement('div');
      this.ui.id = 'job-agent-ui';
      this.ui.innerHTML = this.getUIHTML();
      
      // Add styles
      const style = document.createElement('style');
      style.textContent = this.getUIStyles();
      document.head.appendChild(style);
      
      document.body.appendChild(this.ui);
      
      // Add event listeners
      this.attachUIEventListeners();
      
      this.isVisible = true;
      this.updateUI();
    }

    getUIHTML() {
      return `
        <div class="job-agent-panel">
          <div class="job-agent-header">
            <div class="job-agent-title">
              🤖 Job Agent
              <span class="job-agent-version">v${CONFIG.version}</span>
            </div>
            <button class="job-agent-close" onclick="window.jobAgentBookmarklet.toggleUI()">×</button>
          </div>
          
          <div class="job-agent-content">
            <div class="job-agent-status">
              <div class="status-text" id="job-agent-status">Analyzing page...</div>
            </div>
            
            <div class="job-agent-user-info" id="job-agent-user-info">
              <div class="user-avatar">👤</div>
              <div class="user-details">
                <div class="user-name" id="user-name">Loading...</div>
                <div class="user-email" id="user-email">Loading...</div>
              </div>
            </div>
            
            <div class="job-agent-forms" id="job-agent-forms">
              <!-- Forms will be populated here -->
            </div>
            
            <div class="job-agent-actions">
              <button class="btn btn-primary" onclick="window.jobAgentBookmarklet.fillForm(0)">
                ✨ Auto-Fill Form
              </button>
              <button class="btn btn-secondary" onclick="window.jobAgentBookmarklet.openDashboard()">
                ⚙️ Dashboard
              </button>
            </div>
          </div>
          
          <div class="job-agent-footer">
            <small>Click and drag to move • ESC to close</small>
          </div>
        </div>
      `;
    }

    getUIStyles() {
      return `
        #job-agent-ui {
          all: initial;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          position: fixed;
          top: 20px;
          right: 20px;
          width: 320px;
          z-index: 999999;
          box-shadow: 0 10px 30px rgba(0,0,0,0.3);
          border-radius: 12px;
          overflow: hidden;
          cursor: move;
        }
        
        .job-agent-panel {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 12px;
        }
        
        .job-agent-header {
          padding: 16px 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .job-agent-title {
          font-size: 18px;
          font-weight: 600;
        }
        
        .job-agent-version {
          font-size: 12px;
          opacity: 0.7;
          margin-left: 8px;
        }
        
        .job-agent-close {
          background: none;
          border: none;
          color: white;
          font-size: 24px;
          cursor: pointer;
          padding: 0;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          transition: background 0.2s;
        }
        
        .job-agent-close:hover {
          background: rgba(255,255,255,0.1);
        }
        
        .job-agent-content {
          padding: 20px;
          background: white;
          color: #333;
        }
        
        .job-agent-status {
          margin-bottom: 16px;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 8px;
          text-align: center;
        }
        
        .job-agent-user-info {
          display: flex;
          align-items: center;
          margin-bottom: 16px;
          padding: 12px;
          background: #e3f2fd;
          border-radius: 8px;
        }
        
        .user-avatar {
          font-size: 24px;
          margin-right: 12px;
        }
        
        .user-name {
          font-weight: 600;
          margin-bottom: 4px;
        }
        
        .user-email {
          font-size: 14px;
          color: #666;
        }
        
        .job-agent-forms {
          margin-bottom: 16px;
        }
        
        .form-item {
          padding: 12px;
          background: #f8f9fa;
          border-radius: 8px;
          margin-bottom: 8px;
        }
        
        .form-title {
          font-weight: 600;
          margin-bottom: 8px;
        }
        
        .form-fields {
          font-size: 14px;
          color: #666;
        }
        
        .job-agent-actions {
          display: flex;
          gap: 8px;
        }
        
        .btn {
          flex: 1;
          padding: 12px 16px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }
        
        .btn:hover {
          transform: translateY(-1px);
        }
        
        .btn-primary {
          background: #007bff;
          color: white;
        }
        
        .btn-secondary {
          background: #6c757d;
          color: white;
        }
        
        .job-agent-footer {
          padding: 12px 20px;
          text-align: center;
          font-size: 12px;
          opacity: 0.7;
          border-top: 1px solid rgba(255,255,255,0.2);
        }
        
        .success-message, .error-message {
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 16px;
          font-weight: 600;
        }
        
        .success-message {
          background: #d4edda;
          color: #155724;
        }
        
        .error-message {
          background: #f8d7da;
          color: #721c24;
        }
      `;
    }

    attachUIEventListeners() {
      // Make draggable
      let isDragging = false;
      let dragOffset = { x: 0, y: 0 };
      
      const header = this.ui.querySelector('.job-agent-header');
      
      header.addEventListener('mousedown', (e) => {
        isDragging = true;
        dragOffset.x = e.clientX - this.ui.offsetLeft;
        dragOffset.y = e.clientY - this.ui.offsetTop;
      });
      
      document.addEventListener('mousemove', (e) => {
        if (isDragging) {
          this.ui.style.left = (e.clientX - dragOffset.x) + 'px';
          this.ui.style.top = (e.clientY - dragOffset.y) + 'px';
          this.ui.style.right = 'auto';
        }
      });
      
      document.addEventListener('mouseup', () => {
        isDragging = false;
      });
      
      // ESC key to close
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isVisible) {
          this.toggleUI();
        }
      });
    }

    updateUI() {
      if (!this.ui) return;

      // Update status
      const statusEl = document.getElementById('job-agent-status');
      if (statusEl) {
        if (this.detectedForms.length === 0) {
          statusEl.textContent = 'No job forms detected on this page';
          statusEl.style.color = '#dc3545';
        } else {
          statusEl.textContent = `Found ${this.detectedForms.length} job application form(s)`;
          statusEl.style.color = '#28a745';
        }
      }

      // Update user info
      const nameEl = document.getElementById('user-name');
      const emailEl = document.getElementById('user-email');
      
      if (nameEl && emailEl && userData) {
        nameEl.textContent = `${userData.first_name} ${userData.last_name}`;
        emailEl.textContent = userData.email;
      }

      // Update forms list
      const formsEl = document.getElementById('job-agent-forms');
      if (formsEl && this.detectedForms.length > 0) {
        formsEl.innerHTML = this.detectedForms.map((form, index) => `
          <div class="form-item">
            <div class="form-title">Form ${index + 1}</div>
            <div class="form-fields">${form.fields.length} fields detected</div>
          </div>
        `).join('');
      }
    }

    toggleUI() {
      if (this.ui) {
        this.ui.style.display = this.isVisible ? 'none' : 'block';
        this.isVisible = !this.isVisible;
      }
    }

    openDashboard() {
      window.open(CONFIG.frontendUrl, '_blank');
    }

    showSuccess(message) {
      this.showMessage(message, 'success');
    }

    showError(message) {
      this.showMessage(message, 'error');
    }

    showMessage(message, type) {
      if (!this.ui) return;

      const content = this.ui.querySelector('.job-agent-content');
      const messageEl = document.createElement('div');
      messageEl.className = `${type}-message`;
      messageEl.textContent = message;
      
      content.insertBefore(messageEl, content.firstChild);
      
      setTimeout(() => {
        messageEl.remove();
      }, 5000);
    }
  }

  // Initialize Job Agent
  new JobAgent();

})();