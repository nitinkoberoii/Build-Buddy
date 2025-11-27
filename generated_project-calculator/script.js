// Calculator implementation
class Calculator {
  constructor(displayElement) {
    this.display = displayElement;
    this.currentValue = '';
    this.previousValue = '';
    this.operator = null;
  }

  clear() {
    this.currentValue = '';
    this.previousValue = '';
    this.operator = null;
    this.updateDisplay();
  }

  inputDigit(digit) {
    this.currentValue += digit.toString();
    this.updateDisplay();
  }

  inputDecimal() {
    if (!this.currentValue.includes('.')) {
      this.currentValue += '.';
      this.updateDisplay();
    }
  }

  setOperator(op) {
    if (this.currentValue === '') return;
    if (this.previousValue !== '') {
      this.compute();
    }
    this.operator = op;
    this.previousValue = this.currentValue;
    this.currentValue = '';
    this.updateDisplay();
  }

  compute() {
    if (!this.operator || this.currentValue === '' || this.previousValue === '') return;
    const prev = parseFloat(this.previousValue);
    const current = parseFloat(this.currentValue);
    if (isNaN(prev) || isNaN(current)) return;
    let result;
    switch (this.operator) {
      case '+':
        result = prev + current;
        break;
      case '-':
        result = prev - current;
        break;
      case '*':
        result = prev * current;
        break;
      case '/':
      case '÷':
        if (current === 0) {
          this.currentValue = 'Error';
          this.previousValue = '';
          this.operator = null;
          this.updateDisplay();
          return;
        }
        result = prev / current;
        break;
      default:
        return;
    }
    this.currentValue = result.toString();
    this.previousValue = '';
    this.operator = null;
    this.updateDisplay();
  }

  updateDisplay() {
    if (this.display) {
      this.display.textContent = this.currentValue || '0';
    }
  }
}

// Helper functions for button and key events
function handleButtonClick(event) {
  const button = event.target.closest('.calculator-button');
  if (!button) return;
  const action = button.dataset.action;
  const value = button.dataset.value;
  const calc = window.calculatorInstance;
  if (!calc) return;

  switch (action) {
    case 'number':
      if (value === '.') {
        calc.inputDecimal();
      } else {
        calc.inputDigit(value);
      }
      break;
    case 'operation':
      calc.setOperator(value);
      break;
    case 'equals':
      calc.compute();
      break;
    case 'clear':
      calc.clear();
      break;
    case 'delete':
      // Optional: implement delete if needed
      break;
    default:
      break;
  }
}

function handleKeyPress(event) {
  const key = event.key;
  const calc = window.calculatorInstance;
  if (!calc) return;

  if (key >= '0' && key <= '9') {
    calc.inputDigit(key);
  } else if (key === '.') {
    calc.inputDecimal();
  } else if (['+', '-', '*', '/'].includes(key)) {
    calc.setOperator(key);
  } else if (key === 'Enter' || key === '=') {
    calc.compute();
  } else if (key === 'c' || key === 'C') {
    calc.clear();
  } else if (key === 'Backspace') {
    // Optional: implement delete if needed
  }
}

// Initialize calculator after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const displayElement = document.querySelector('#display');
  const calculator = new Calculator(displayElement);
  // Store instance globally for event handlers
  window.calculatorInstance = calculator;

  // Attach button click listeners
  document.querySelectorAll('.calculator-button').forEach(btn => {
    btn.addEventListener('click', handleButtonClick);
  });

  // Attach keyboard listener
  document.addEventListener('keydown', handleKeyPress);
});
