-- Create Projects Table
create table public.projects (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) not null,
  project_name text not null,
  city text not null,
  project_type text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  -- Analysis Data (Storing JSONB for flexibility)
  input_data jsonb not null,
  analysis_result jsonb not null,
  
  -- Quick Access fields (optional, for sorting/filtering without digging into JSON)
  overall_score numeric,
  impact_class text
);

-- RLS Policies
alter table public.projects enable row level security;

create policy "Users can view their own projects"
on public.projects for select
using (auth.uid() = user_id);

create policy "Users can insert their own projects"
on public.projects for insert
with check (auth.uid() = user_id);

create policy "Users can update their own projects"
on public.projects for update
using (auth.uid() = user_id);

create policy "Users can delete their own projects"
on public.projects for delete
using (auth.uid() = user_id);
