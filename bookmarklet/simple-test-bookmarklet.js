// Simple test bookmarklet to verify basic functionality
javascript:(function(){
  alert('🤖 Job Agent Test - Bookmarklet is working!');
  
  // Test basic form detection
  const forms = document.querySelectorAll('form');
  const inputs = document.querySelectorAll('input[type="text"], input[type="email"], textarea');
  
  console.log('Forms found:', forms.length);
  console.log('Input fields found:', inputs.length);
  
  // Create a simple popup
  const popup = document.createElement('div');
  popup.id = 'test-popup';
  popup.innerHTML = `
    <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
         background: white; padding: 20px; border: 2px solid #007bff; border-radius: 10px; 
         box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 999999; font-family: Arial;">
      <h3>🤖 Job Agent Test</h3>
      <p>Forms found: ${forms.length}</p>
      <p>Input fields found: ${inputs.length}</p>
      <button onclick="document.getElementById('test-popup').remove();" 
              style="background: #007bff; color: white; border: none; padding: 10px 20px; 
                     border-radius: 5px; cursor: pointer;">Close</button>
    </div>
  `;
  
  document.body.appendChild(popup);
})();