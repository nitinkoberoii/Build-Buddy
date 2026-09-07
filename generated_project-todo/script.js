// Placeholder for future JavaScript enhancements
// Define a greet function that logs the text content of the element with id 'greeting'

function greet() {
  const greeting = document.getElementById('greeting');
  if (greeting) {
    console.log(greeting.textContent);
  } else {
    console.warn("Element with id 'greeting' not found.");
  }
}

// Call greet on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', greet);
} else {
  greet();
}

// If this script is used as a module, export the greet function
// (Uncomment the following line when using <script type="module" src="script.js"></script>)
// export { greet };
