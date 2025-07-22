// Working Job Agent Bookmarklet - Step by step build
javascript:(function(){
  'use strict';
  
  // Prevent multiple instances
  if (window.jobAgent) {
    window.jobAgent.toggle();
    return;
  }
  
  console.log('🤖 Job Agent starting...');
  
  // User data
  const userData = {
    email: 'jane@email.com',
    first_name: 'Jane', 
    last_name: 'Doe',
    phone: '+1 (555) 123-4567',
    linkedin_url: 'https://linkedin.com/in/janedoe',
    location: 'San Francisco, CA'
  };
  
  // Main class
  class JobAgent {
    constructor() {
      this.forms = [];
      this.visible = false;
      this.ui = null;
      this.init();
    }
    
    init() {
      this.detectForms();
      this.createUI();
      this.visible = true;
      console.log('Found', this.forms.length, 'job forms');
    }
    
    detectForms() {
      // Get all forms
      const allForms = document.querySelectorAll('form');
      
      allForms.forEach((form, i) => {
        const text = form.textContent.toLowerCase();
        const jobWords = ['name', 'email', 'phone', 'resume', 'apply', 'job'];
        const matches = jobWords.filter(word => text.includes(word)).length;
        
        if (matches >= 3) {
          const fields = this.getFields(form);
          this.forms.push({
            element: form,
            fields: fields,
            index: i
          });
        }
      });
      
      // If no forms, look for standalone inputs (SPA style)
      if (this.forms.length === 0) {
        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], textarea, select');
        if (inputs.length > 3) {
          const fields = Array.from(inputs).map(this.analyzeField.bind(this));
          this.forms.push({
            element: document.body,
            fields: fields,
            index: 0,
            virtual: true
          });
        }
      }
    }
    
    getFields(form) {
      const inputs = form.querySelectorAll('input, textarea, select');
      return Array.from(inputs)
        .filter(input => !['hidden', 'submit', 'button'].includes(input.type))
        .map(this.analyzeField.bind(this));
    }
    
    analyzeField(input) {
      const label = this.getLabel(input);
      const type = this.getFieldType(input, label);
      
      return {
        element: input,
        label: label,
        type: type,
        name: input.name || input.id || 'field'
      };
    }
    
    getLabel(input) {
      // Try different ways to find label
      if (input.id) {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label) return label.textContent.trim();
      }
      
      const parent = input.closest('label');
      if (parent) return parent.textContent.trim();
      
      const prev = input.previousElementSibling;
      if (prev && prev.tagName === 'LABEL') {
        return prev.textContent.trim();
      }
      
      return input.placeholder || input.name || 'Unknown';
    }
    
    getFieldType(input, label) {
      const text = (label + ' ' + input.name + ' ' + input.placeholder).toLowerCase();
      
      if (text.includes('email')) return 'email';
      if (text.includes('first') && text.includes('name')) return 'firstName';
      if (text.includes('last') && text.includes('name')) return 'lastName';
      if (text.includes('phone')) return 'phone';
      if (text.includes('linkedin')) return 'linkedin';
      if (text.includes('location') || text.includes('city')) return 'location';
      
      return 'other';
    }
    
    fillForm() {
      if (this.forms.length === 0) {
        alert('No forms found to fill');
        return;
      }
      
      const form = this.forms[0];
      let filled = 0;
      
      form.fields.forEach(field => {
        const value = this.getValue(field.type);
        if (value && field.element) {
          field.element.value = value;
          field.element.dispatchEvent(new Event('input', {bubbles: true}));
          field.element.dispatchEvent(new Event('change', {bubbles: true}));
          
          // Visual feedback
          field.element.style.backgroundColor = '#d4edda';
          setTimeout(() => {
            field.element.style.backgroundColor = '';
          }, 1500);
          
          filled++;
        }
      });
      
      alert(`Filled ${filled} fields out of ${form.fields.length}`);
    }
    
    getValue(fieldType) {
      const mapping = {
        'email': userData.email,
        'firstName': userData.first_name,
        'lastName': userData.last_name,
        'phone': userData.phone,
        'linkedin': userData.linkedin_url,
        'location': userData.location
      };
      
      return mapping[fieldType] || '';
    }
    
    createUI() {
      // Remove existing
      const existing = document.getElementById('job-agent-ui');
      if (existing) existing.remove();
      
      this.ui = document.createElement('div');
      this.ui.id = 'job-agent-ui';
      this.ui.innerHTML = `
        <div style="position: fixed; top: 20px; right: 20px; width: 300px; 
                    background: linear-gradient(135deg, #667eea, #764ba2); 
                    border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    color: white; font-family: Arial, sans-serif; z-index: 999999;">
          
          <div style="padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.2); 
                      display: flex; justify-content: space-between; align-items: center;">
            <div style="font-weight: bold;">🤖 Job Agent</div>
            <button onclick="window.jobAgent.toggle()" 
                    style="background: none; border: none; color: white; font-size: 20px; cursor: pointer;">×</button>
          </div>
          
          <div style="padding: 20px; background: white; color: #333; border-radius: 0 0 12px 12px;">
            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; text-align: center;">
              <strong>${this.forms.length} job form(s) detected</strong>
            </div>
            
            <div style="margin-bottom: 15px; padding: 10px; background: #e3f2fd; border-radius: 6px; display: flex; align-items: center;">
              <div style="margin-right: 10px;">👤</div>
              <div>
                <div style="font-weight: bold;">${userData.first_name} ${userData.last_name}</div>
                <div style="font-size: 14px; color: #666;">${userData.email}</div>
              </div>
            </div>
            
            <button onclick="window.jobAgent.fillForm()" 
                    style="width: 100%; padding: 12px; background: #007bff; color: white; 
                           border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
              ✨ Auto-Fill Form
            </button>
          </div>
        </div>
      `;
      
      document.body.appendChild(this.ui);
    }
    
    toggle() {
      if (this.ui) {
        this.ui.style.display = this.visible ? 'none' : 'block';
        this.visible = !this.visible;
      }
    }
  }
  
  // Initialize
  window.jobAgent = new JobAgent();
})();