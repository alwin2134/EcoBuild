const SUPABASE_URL = "https://krifcbhqqxltpgdhvwhz.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtyaWZjYmhxcXhsdHBnZGh2d2h6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2MzU3ODIsImV4cCI6MjA4MTIxMTc4Mn0.jPbddcNlyNKQ75kBEl_a8972-jhb3KQa0UeszSkGA90";

// API Base URL - automatically detects local vs production
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : window.location.origin; // Use same origin when deployed

const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
window.supabaseClient = client;
window.API_BASE_URL = API_BASE_URL;
