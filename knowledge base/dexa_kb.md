# JavaScript Knowledge Base

> A comprehensive reference to JavaScript for code generation tools.

---

## 📌 1. Introduction

JavaScript is a versatile, high-level scripting language primarily used for web development. It runs in web browsers and on servers using Node.js.

---

## 📌 2. Variables

Variables are used to store data values.

### 🔸 Declarations:

* `var`: Function-scoped
* `let`: Block-scoped (preferred)
* `const`: Block-scoped and immutable

### ✅ Examples:

```js
var name = "Alice";
let age = 25;
const country = "India";
```

---

## 📌 3. Data Types

JavaScript supports the following types:

* String
* Number
* Boolean
* Null
* Undefined
* Object
* Array
* Function
* Symbol (ES6)
* BigInt (ES11)

### ✅ Examples:

```js
let message = "Hello, world";     // String
let count = 42;                   // Number
let isReady = true;               // Boolean
let unknown = undefined;          // Undefined
let nothing = null;               // Null
let person = { name: "John" };    // Object
let list = [1, 2, 3];             // Array
let greet = function() {};        // Function
```

---

## 📌 4. Operators

### 🔸 Arithmetic Operators:

```js
let a = 10 + 5;     // 15
let b = 10 - 5;     // 5
let c = 10 * 2;     // 20
let d = 10 / 2;     // 5
let e = 10 % 3;     // 1
```

### 🔸 Comparison Operators:

```js
5 == "5";       // true
5 === "5";      // false
10 != 8;        // true
10 !== "10";    // true
```

### 🔸 Logical Operators:

```js
true && false;  // false
true || false;  // true
!true;          // false
```

### 🔸 Assignment Operators:

```js
let x = 5;
x += 2;  // x = 7
x *= 3;  // x = 21
```

---

## 📌 5. Conditionals

### 🔸 if Statement:

```js
let age = 20;

if (age >= 18) {
  console.log("You are an adult.");
}
```

### 🔸 if-else:

```js
let temperature = 15;

if (temperature > 30) {
  console.log("Hot");
} else {
  console.log("Cool");
}
```

### 🔸 if-else if:

```js
let marks = 75;

if (marks >= 90) {
  console.log("Grade A");
} else if (marks >= 70) {
  console.log("Grade B");
} else {
  console.log("Grade C");
}
```

### 🔸 Ternary Operator:

```js
let result = (age >= 18) ? "Adult" : "Minor";
console.log(result); // Adult
```

---

## 📌 6. Loops

### 🔸 for Loop:

```js
for (let i = 0; i < 5; i++) {
  console.log(i);
}
```

### 🔸 while Loop:

```js
let i = 0;
while (i < 5) {
  console.log(i);
  i++;
}
```

### 🔸 do...while Loop:

```js
let i = 0;
do {
  console.log(i);
  i++;
} while (i < 5);
```

### 🔸 for...of (for arrays):

```js
let arr = ["a", "b", "c"];
for (let item of arr) {
  console.log(item);
}
```

### 🔸 for...in (for objects):

```js
let obj = { a: 1, b: 2 };
for (let key in obj) {
  console.log(key, obj[key]);
}
```

---

## 📌 7. Functions

### 🔸 Function Declaration:

```js
function add(a, b) {
  return a + b;
}
```

### 🔸 Function Expression:

```js
const subtract = function(a, b) {
  return a - b;
};
```

### 🔸 Arrow Functions:

```js
const multiply = (a, b) => a * b;
```

---

## 📌 8. Arrays

### 🔸 Declaring an Array:

```js
let numbers = [1, 2, 3, 4];
```

### 🔸 Common Methods:

```js
numbers.push(5);     // Add to end
numbers.pop();       // Remove from end
numbers.shift();     // Remove from start
numbers.unshift(0);  // Add to start

let doubled = numbers.map(n => n * 2);
let evens = numbers.filter(n => n % 2 === 0);
```

---

## 📌 9. Objects

### 🔸 Defining an Object:

```js
let person = {
  name: "Alice",
  age: 30,
  greet: function() {
    console.log("Hello");
  }
};
```

### 🔸 Accessing Properties:

```js
console.log(person.name);   // Alice
console.log(person["age"]); // 30
```

### 🔸 Updating:

```js
person.age = 31;
person.city = "New York";
```

---

## 📌 10. ES6+ Features

### 🔸 Destructuring:

```js
const person = { name: "Bob", age: 25 };
const { name, age } = person;
```

### 🔸 Spread & Rest:

```js
const arr1 = [1, 2];
const arr2 = [...arr1, 3, 4];

function sum(...nums) {
  return nums.reduce((a, b) => a + b);
}
```

### 🔸 Template Literals:

```js
const greeting = `Hello, ${name}`;
```

### 🔸 Default Parameters:

```js
function greet(name = "Guest") {
  console.log("Hello " + name);
}
```

---

## 📌 11. Error Handling

### 🔸 try...catch:

```js
try {
  throw new Error("Something went wrong");
} catch (error) {
  console.log(error.message);
}
```

---

## 📌 12. JSON

### 🔸 Parse JSON:

```js
const jsonStr = '{"name":"Alice","age":30}';
const obj = JSON.parse(jsonStr);
```

### 🔸 Stringify Object:

```js
const str = JSON.stringify(obj);
```

---

## 📌 13. Promises & Async

### 🔸 Promises:

```js
function fetchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => resolve("Data Loaded"), 1000);
  });
}
```

### 🔸 Async/Await:

```js
async function getData() {
  const data = await fetchData();
  console.log(data);
}
```

---

## 📌 14. DOM Basics

### 🔸 Select Elements:

```js
document.getElementById("id");
document.querySelector(".class");
```

### 🔸 Manipulate Elements:

```js
const el = document.getElementById("myDiv");
el.innerText = "Hello!";
el.style.color = "red";
```

---

## 📌 15. Event Handling

### 🔸 Add Event Listener:

```js
const btn = document.getElementById("btn");
btn.addEventListener("click", function() {
  alert("Button clicked!");
});
```

---

## 📌 16. Modules (ES6)

### 🔸 Export:

```js
export const name = "JS";
export function add(a, b) { return a + b; }
```

### 🔸 Import:

```js
import { name, add } from './utils.js';
```

---

## 📌 17. Classes (ES6)

### 🔸 Define a Class:

```js
class Person {
  constructor(name, age) {
    this.name = name;
    this.age = age;
  }

  greet() {
    console.log(`Hello, I'm ${this.name}`);
  }
}

const p1 = new Person("Alice", 25);
p1.greet();
```

---

# JavaScript Knowledge Base

> A comprehensive reference to JavaScript for code generation tools.

---

## 📌 Using This Knowledge Base to Write JavaScript Programs

This knowledge base is designed to help automated systems, developers, or code generators write JavaScript programs correctly and efficiently. Here's how to use this document:

* Use **syntax patterns** and **code templates** as building blocks.
* Refer to **examples** to understand structure and logic.
* Follow best practices to avoid bugs and improve performance.

> ✅ DO NOT repeat previously defined sections. Only expand with **new content and patterns** useful for generating JavaScript code.

---

## 📌 Helper Patterns and Techniques for Code Writing

### 🔹 Common Syntax Structures

**Variable Declaration Pattern:**

```js
let <name> = <value>;       // Mutable
const <name> = <value>;     // Immutable
```

**Function Declaration Pattern:**

```js
function <functionName>(<params>) {
  // logic
  return <result>;
}
```

**Arrow Function Pattern:**

```js
const <name> = (<params>) => {
  // logic
};
```

**Object Creation Pattern:**

```js
const obj = {
  key1: value1,
  key2: value2,
};
```

**Array Iteration (forEach):**

```js
array.forEach(item => {
  console.log(item);
});
```

**Array Iteration (map):**

```js
const newArray = array.map(item => item + 1);
```

### 🔹 Input/Output Patterns

**Print to Console:**

```js
console.log("Message");
```

**User Input (browser):**

```js
let name = prompt("Enter your name:");
```

**Output to DOM:**

```js
document.getElementById("output").innerText = "Result";
```

---

## 📌 Template Snippets for Common Tasks

### 🧩 1. Swap Two Variables

```js
let a = 10, b = 20;
[a, b] = [b, a];
```

### 🧩 2. Check Prime Number

```js
function isPrime(num) {
  if (num <= 1) return false;
  for (let i = 2; i < num; i++) {
    if (num % i === 0) return false;
  }
  return true;
}
```

### 🧩 3. Reverse a String

```js
function reverseString(str) {
  return str.split("").reverse().join("");
}
```

### 🧩 4. Capitalize Each Word

```js
function capitalizeWords(sentence) {
  return sentence.split(" ")
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
```

---

## 📌 Writing Flow for Any JavaScript Program

1. **Understand the Requirement:**

   * Identify input/output
   * Understand logic (loop, condition, data structure)

2. **Use Syntax Patterns:**

   * Start from templates above
   * Choose right structure (loop, function, class)

3. **Write Modular Code:**

   * Use functions to break logic into steps

4. **Use Console/DOM to Show Output**

5. **Test with Example Inputs**

---

## 📌 Best Practices

* Always use `let` and `const`, avoid `var`
* Keep functions small and specific
* Use `===` for strict equality
* Use template literals: `Hello, ${name}`
* Use arrow functions for short logic
* Use `map`, `filter`, `reduce` for array transformations

---

## 📌 How This Helps Code Generation

When asked to generate JavaScript code:

* Find relevant task pattern (e.g., string reversal)
* Follow syntax structures
* Fill placeholders (`<value>`, `<param>`, `<logic>`) with correct details
* Ensure code is functional, complete, and testable

> Example Prompt: **"Write a function to capitalize each word in a sentence"**
> → Refer to `capitalizeWords(...)` snippet

---

## ✅ Next Topics to Expand

* DOM Manipulation
* Event Handling
* Fetch API / Ajax
* ES6+ Features (Destructuring, Spread, etc.)
* Classes & Modules
* Error Handling



---
