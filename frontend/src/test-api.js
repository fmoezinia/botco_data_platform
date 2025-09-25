// Simple test to check if API is working
fetch('http://localhost:8000/scenarios-list')
  .then(response => response.json())
  .then(data => console.log('API Test Result:', data))
  .catch(error => console.error('API Test Error:', error));
