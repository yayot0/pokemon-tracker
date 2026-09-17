/** @type {import('tailwindcss').Config} */
export default {
content: ["./index.html", "./src/**/*.{js,jsx}"],
theme: {
    extend: {
    colors: {
        ink: "#0F1024",
        surface: "#181A38",
        "surface-alt": "#22254A",
        border: "#33366A",
        gold: "#D4AF37",
        text: "#EDEAE0",
        "text-muted": "#8B8FB0",
        gain: "#4ADE80",
        loss: "#F87171",
    },
    fontFamily: {
        display: ["Space Grotesk", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
    },
    },
},
plugins: [],
};