const SUPABASE_URL = "https://krifcbhqqxltpgdhvwhz.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtyaWZjYmhxcXhsdHBnZGh2d2h6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2MzU3ODIsImV4cCI6MjA4MTIxMTc4Mn0.jPbddcNlyNKQ75kBEl_a8972-jhb3KQa0UeszSkGA90";

const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
window.supabaseClient = client;
