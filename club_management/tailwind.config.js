/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Main templates directory
    "./templates/**/*.html",
    
    // App-specific templates (add all your apps here)
    "./Events/templates/**/*.html",
    "./clubs/templates/**/*.html", 
    "./Applications/templates/**/*.html",
    "./users/templates/**/*.html",
    // "./myapp/templates/**/*.html",
    
    // Generic pattern to catch any app templates
    "./**/templates/**/*.html",
    
    // Include JavaScript files if you have dynamic classes
    "./**/static/**/*.js",

    "./node_modules/flowbite/**/*.js"

  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('flowbite/plugin')

  ],
}