// Self-contained Job Agent Bookmarklet - No external dependencies
// This entire script runs inline to bypass CSP restrictions

javascript:(function(){
  'use strict';

  // Prevent multiple instances
  if (window.jobAgentBookmarklet) {
    window.jobAgentBookmarklet.toggleUI();
    return;
  }

  // Configuration
  const CONFIG = {
    apiBaseUrl: 'http://localhost:8000',
    frontendUrl: 'http://localhost:3000',
    version: '1.0.0'
  };

  // Demo user data (fallback)
  let userData = {
    email: 'jane@email.com',
    first_name: 'Jane',
    last_name: 'Doe',
    phone: '+1 (555) 123-4567',
    linkedin_url: 'https://linkedin.com/in/janedoe',
    portfolio_url: 'https://janedoe.dev',
    location: 'San Francisco, CA'
  };

  // Job Agent Class
  class JobAgent {
    constructor() {
      this.detectedForms = [];
      this.isVisible = false;
      this.ui = null;
      this.init();
    }

    async init() {
      console.log('🤖 Job Agent v' + CONFIG.version);
      window.jobAgentBookmarklet = this;

      try {
        await this.loadAuth();
        this.detectJobForms();
        this.createUI();
        console.log('Found ' + this.detectedForms.length + ' job forms');
      } catch (error) {
        console.error('Job Agent error:', error);
        this.showError('Failed to initialize: ' + error.message);
      }
    }

    async loadAuth() {
      // Try localStorage first
      try {
        const authToken = localStorage.getItem('auth_token');
        if (authToken) {
          const authData = JSON.parse(authToken);
          if (authData.access_token && authData.user) {
            userData = authData.user;
            console.log('✅ Loaded auth from localStorage');
            return;
          }
        }
      } catch (e) {
        console.log('No auth in localStorage');
      }

      // Try backend auth
      try {
        const response = await fetch(CONFIG.apiBaseUrl + '/api/auth/login', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({email: 'jane@email.com', password: 'testpass123'})
        });
        
        if (response.ok) {
          const authData = await response.json();
          userData = authData.user;
          console.log('✅ Authenticated with backend');
        }
      } catch (error) {
        console.log('Using demo data');
      }
    }

    detectJobForms() {
      this.detectedForms = [];

      // Check traditional forms
      const forms = document.querySelectorAll('form');
      forms.forEach((form, index) => {
        const formData = this.analyzeForm(form, index);
        if (formData && formData.isJobForm) {
          this.detectedForms.push(formData);
        }
      });

      // Check for standalone inputs (SPAs)
      if (this.detectedForms.length === 0) {
        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], textarea, select');
        if (inputs.length > 3) {
          const virtualForm = this.createVirtualForm(inputs);
          if (virtualForm) this.detectedForms.push(virtualForm);
        }
      }
    }

    analyzeForm(form, index) {
      const text = form.textContent.toLowerCase();
      const html = form.innerHTML.toLowerCase();
      
      const jobKeywords = [
        'resume', 'cv', 'application', 'apply', 'job', 'career',
        'first name', 'last name', 'email', 'phone', 'linkedin'
      ];

      const score = jobKeywords.filter(keyword => 
        text.includes(keyword) || html.includes(keyword)
      ).length;

      if (score < 3) return null;

      return {
        index: index,
        element: form,
        fields: this.extractFormFields(form),
        isJobForm: true,
        confidence: Math.min(score / 10, 1.0)
      };
    }

    createVirtualForm(inputs) {
      const fields = [];
      
      Array.from(inputs).forEach((input, index) => {
        const field = this.analyzeField(input, index);
        if (field) fields.push(field);
      });

      if (fields.length < 3) return null;

      return {
        index: 0,
        element: document.body,
        fields: fields,
        isJobForm: true,
        confidence: 0.8,
        isVirtual: true
      };
    }

    extractFormFields(form) {
      const fields = [];
      const inputs = form.querySelectorAll('input, textarea, select');
      
      inputs.forEach((input, index) => {
        if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') return;
        const field = this.analyzeField(input, index);
        if (field) fields.push(field);
      });

      return fields;
    }

    analyzeField(input, index) {
      const label = this.findLabelForInput(input);
      const fieldType = this.classifyFieldType(input, label);
      
      return {
        id: input.id || 'field_' + index,
        name: input.name || input.id || 'field_' + index,
        type: input.type || input.tagName.toLowerCase(),
        label: label,
        placeholder: input.placeholder || '',
        element: input,
        fieldType: fieldType
      };
    }

    findLabelForInput(input) {
      // Direct label
      if (input.id) {
        const label = document.querySelector('label[for="' + input.id + '"]');
        if (label) return label.textContent.trim();
      }
      
      // Parent label
      const parentLabel = input.closest('label');
      if (parentLabel) return parentLabel.textContent.trim();
      
      // Previous sibling
      const prevSibling = input.previousElementSibling;
      if (prevSibling && (prevSibling.tagName === 'LABEL' || prevSibling.tagName === 'SPAN')) {
        return prevSibling.textContent.trim();
      }
      
      return input.placeholder || this.humanizeFieldName(input.name) || 'Unknown field';
    }

    classifyFieldType(input, label) {
      const text = (input.name + ' ' + label + ' ' + input.placeholder).toLowerCase();
      
      if (text.includes('email')) return 'email';
      if (text.includes('first name') || text.includes('fname')) return 'firstName';
      if (text.includes('last name') || text.includes('lname')) return 'lastName';
      if (text.includes('full name') || text.includes('name')) return 'fullName';
      if (text.includes('phone') || text.includes('mobile')) return 'phone';
      if (text.includes('linkedin')) return 'linkedin';
      if (text.includes('portfolio') || text.includes('website')) return 'portfolio';
      if (text.includes('location') || text.includes('city')) return 'location';
      
      return 'other';
    }

    humanizeFieldName(name) {
      if (!name) return '';
      return name.replace(/[_-]/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
        .toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
    }

    async fillForm(formIndex = 0) {
      if (!this.detectedForms[formIndex]) {
        this.showError('No form found');
        return;
      }

      const form = this.detectedForms[formIndex];
      let filledCount = 0;

      for (const field of form.fields) {
        const value = this.mapUserDataToField(field);
        if (value && field.element) {
          try {
            field.element.value = value;
            field.element.dispatchEvent(new Event('input', { bubbles: true }));
            field.element.dispatchEvent(new Event('change', { bubbles: true }));
            this.highlightField(field.element, 'success');
            filledCount++;
          } catch (error) {
            this.highlightField(field.element, 'error');
          }
        }
      }

      this.showSuccess('Filled ' + filledCount + ' of ' + form.fields.length + ' fields');
      this.updateUI();
    }

    mapUserDataToField(field) {
      const mapping = {
        'email': userData.email,
        'firstName': userData.first_name,
        'lastName': userData.last_name,
        'fullName': (userData.first_name + ' ' + userData.last_name).trim(),
        'phone': userData.phone,
        'linkedin': userData.linkedin_url,
        'portfolio': userData.portfolio_url || userData.website_url,
        'location': userData.location
      };

      return mapping[field.fieldType] || '';
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
      const existing = document.getElementById('job-agent-ui');
      if (existing) existing.remove();

      this.ui = document.createElement('div');
      this.ui.id = 'job-agent-ui';
      this.ui.innerHTML = this.getUIHTML();
      
      const style = document.createElement('style');
      style.textContent = this.getUIStyles();
      document.head.appendChild(style);
      
      document.body.appendChild(this.ui);
      this.attachUIEventListeners();
      this.isVisible = true;
      this.updateUI();
    }

    getUIHTML() {
      return '<div class="job-agent-panel">' +
        '<div class="job-agent-header">' +
          '<div class="job-agent-title">🤖 Job Agent <span class="job-agent-version">v' + CONFIG.version + '</span></div>' +
          '<button class="job-agent-close" onclick="window.jobAgentBookmarklet.toggleUI()">×</button>' +
        '</div>' +
        '<div class="job-agent-content">' +
          '<div class="job-agent-status"><div class="status-text" id="job-agent-status">Analyzing...</div></div>' +
          '<div class="job-agent-user-info">' +
            '<div class="user-avatar">👤</div>' +
            '<div class="user-details">' +
              '<div class="user-name">' + userData.first_name + ' ' + userData.last_name + '</div>' +
              '<div class="user-email">' + userData.email + '</div>' +
            '</div>' +
          '</div>' +
          '<div class="job-agent-forms" id="job-agent-forms"></div>' +
          '<div class="job-agent-actions">' +
            '<button class="btn btn-primary" onclick="window.jobAgentBookmarklet.fillForm(0)">✨ Auto-Fill Form</button>' +
            '<button class="btn btn-secondary" onclick="window.open(\'' + CONFIG.frontendUrl + '\', \'_blank\')">⚙️ Dashboard</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    }

    getUIStyles() {
      return '#job-agent-ui{all:initial;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;position:fixed;top:20px;right:20px;width:320px;z-index:999999;box-shadow:0 10px 30px rgba(0,0,0,0.3);border-radius:12px;overflow:hidden;cursor:move}' +
      '.job-agent-panel{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border-radius:12px}' +
      '.job-agent-header{padding:16px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(255,255,255,0.2)}' +
      '.job-agent-title{font-size:18px;font-weight:600}' +
      '.job-agent-version{font-size:12px;opacity:0.7;margin-left:8px}' +
      '.job-agent-close{background:none;border:none;color:white;font-size:24px;cursor:pointer;padding:0;width:30px;height:30px;display:flex;align-items:center;justify-content:center;border-radius:50%;transition:background 0.2s}' +
      '.job-agent-close:hover{background:rgba(255,255,255,0.1)}' +
      '.job-agent-content{padding:20px;background:white;color:#333}' +
      '.job-agent-status{margin-bottom:16px;padding:12px;background:#f8f9fa;border-radius:8px;text-align:center}' +
      '.job-agent-user-info{display:flex;align-items:center;margin-bottom:16px;padding:12px;background:#e3f2fd;border-radius:8px}' +
      '.user-avatar{font-size:24px;margin-right:12px}' +
      '.user-name{font-weight:600;margin-bottom:4px}' +
      '.user-email{font-size:14px;color:#666}' +
      '.job-agent-actions{display:flex;gap:8px}' +
      '.btn{flex:1;padding:12px 16px;border:none;border-radius:8px;font-weight:600;cursor:pointer;transition:transform 0.2s}' +
      '.btn:hover{transform:translateY(-1px)}' +
      '.btn-primary{background:#007bff;color:white}' +
      '.btn-secondary{background:#6c757d;color:white}' +
      '.success-message,.error-message{padding:12px;border-radius:8px;margin-bottom:16px;font-weight:600}' +
      '.success-message{background:#d4edda;color:#155724}' +
      '.error-message{background:#f8d7da;color:#721c24}';
    }

    attachUIEventListeners() {
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
      
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isVisible) {
          this.toggleUI();
        }
      });
    }

    updateUI() {
      const statusEl = document.getElementById('job-agent-status');
      if (statusEl) {
        if (this.detectedForms.length === 0) {
          statusEl.textContent = 'No job forms detected';
          statusEl.style.color = '#dc3545';
        } else {
          statusEl.textContent = 'Found ' + this.detectedForms.length + ' job form(s)';
          statusEl.style.color = '#28a745';
        }
      }

      const formsEl = document.getElementById('job-agent-forms');
      if (formsEl && this.detectedForms.length > 0) {
        formsEl.innerHTML = this.detectedForms.map((form, index) => 
          '<div style="padding:8px;background:#f8f9fa;border-radius:4px;margin:8px 0">Form ' + (index + 1) + ': ' + form.fields.length + ' fields</div>'
        ).join('');
      }
    }

    toggleUI() {
      if (this.ui) {
        this.ui.style.display = this.isVisible ? 'none' : 'block';
        this.isVisible = !this.isVisible;
      }
    }

    showSuccess(message) { this.showMessage(message, 'success'); }
    showError(message) { this.showMessage(message, 'error'); }

    showMessage(message, type) {
      if (!this.ui) return;
      const content = this.ui.querySelector('.job-agent-content');
      const messageEl = document.createElement('div');
      messageEl.className = type + '-message';
      messageEl.textContent = message;
      content.insertBefore(messageEl, content.firstChild);
      setTimeout(() => messageEl.remove(), 5000);
    }
  }

  new JobAgent();
})();